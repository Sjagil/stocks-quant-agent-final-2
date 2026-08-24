from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .cost_evidence_producer_v2_39_3 import produce_cost_stress_from_oos
from .evidence_production_contracts_v2_39_3 import (
    EvidenceProductionResultV2393,
    OOSProductionResultV2393,
    ProductionInputAuditV2393,
)
from .evidence_production_ingest_v2_39_3 import ingest_produced_evidence
from .external_oos_evidence_v2_39_3 import load_external_observations
from .factory_oos_replay_v2_39_3 import audit_factory_replay_inputs, replay_factory_oos
from .health_v2_39_2 import assess_entity_hardened_v2392
from .oos_observation_validation_v2_39_3 import (
    effective_nonoverlap_observations,
    normalize_oos_observations,
    profit_factor,
    write_json,
)
from .store_v2_39 import ResearchStoreV239


def load_production_config(project_root: Path, config_path: str | Path | None = None) -> dict:
    path = Path(config_path) if config_path else project_root / "config/research_evidence_production_v2_39_3.json"
    if not path.is_absolute():
        path = project_root / path
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("execution_authority") != "NONE":
        raise ValueError("evidence production cannot have execution authority")
    if cfg.get("broker_submission_enabled") or cfg.get("automatic_live_promotion") or cfg.get("automatic_champion_promotion"):
        raise ValueError("unsafe evidence production configuration")
    return cfg


def load_continuous_config(project_root: Path, production_cfg: dict) -> dict:
    path = project_root / str(production_cfg.get("continuous_config", "config/continuous_quant_research_v2_39_2.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_paths(project_root: Path, production_cfg: dict, continuous_cfg: dict) -> tuple[Path, Path, Path]:
    continuous_root = project_root / str(continuous_cfg["runtime_root"])
    db = continuous_root / str(continuous_cfg.get("database_name", "research.db"))
    output = continuous_root / str(production_cfg.get("runtime_subdir", "evidence_production_v2_39_3"))
    return continuous_root, db, output


def _assessment(store: ResearchStoreV239, entity_id: str, continuous_cfg: dict) -> dict:
    return assess_entity_hardened_v2392(
        store,
        entity_id,
        policy=continuous_cfg["health"],
        bayesian=continuous_cfg["bayesian"],
        quality_weights=continuous_cfg["quality_weights"],
    ).as_dict()


def audit_entity_inputs(project_root: Path, store: ResearchStoreV239, entity_id: str, *, production_cfg: dict) -> ProductionInputAuditV2393:
    entity = store.get_entity(entity_id)
    if entity is None:
        return ProductionInputAuditV2393(entity_id, "NONE", "BLOCKED", False, ("ENTITY_NOT_FOUND",), {})
    if entity.get("entity_type") != "STRATEGY":
        return ProductionInputAuditV2393(entity_id, "NONE", "BLOCKED", False, ("UNSUPPORTED_ENTITY_TYPE",), {})
    return audit_factory_replay_inputs(project_root, entity, config=production_cfg["factory_1h"])


def _produce_observation_evidence(
    project_root: Path,
    store: ResearchStoreV239,
    entity_id: str,
    *,
    observations: pd.DataFrame,
    provenance: dict,
    input_audit: ProductionInputAuditV2393,
    production_cfg: dict,
    continuous_cfg: dict,
    before: dict | None,
) -> EvidenceProductionResultV2393:
    _, _, output_root = runtime_paths(project_root, production_cfg, continuous_cfg)
    safe_id = entity_id.replace(":", "__").replace("/", "_")
    output_dir = output_root / safe_id
    output_dir.mkdir(parents=True, exist_ok=True)
    hid = entity_id.split(":", 1)[1]
    observations = normalize_oos_observations(observations, entity_hypothesis_id=hid)
    raw_trades = int(len(observations))
    effective = effective_nonoverlap_observations(observations)
    min_effective = int(production_cfg.get("minimum_effective_oos_observations", 60))
    min_raw = int(production_cfg.get("minimum_raw_oos_trades", min_effective))
    base_cost = float(provenance["base_cost_bps_per_side"])
    if not math.isfinite(base_cost) or base_cost < 0:
        raise ValueError("base_cost_bps_per_side must be finite and nonnegative")
    gross = pd.to_numeric(observations.get("gross_return", pd.Series(dtype=float)), errors="coerce").to_numpy(dtype=float)
    gross = gross[np.isfinite(gross)]
    cost = base_cost / 10_000.0
    net = (1.0 + gross) * (1.0 - cost) / (1.0 + cost) - 1.0 if len(gross) else np.asarray([], dtype=float)
    expectancy = float(np.mean(net)) if len(net) else math.nan
    pf = float(profit_factor(net)) if len(net) else math.nan
    oos_pass = bool(raw_trades >= min_raw and effective >= min_effective and np.isfinite(expectancy) and expectancy > 0)

    obs_path = output_dir / "oos_observations.csv"
    observations.to_csv(obs_path, index=False)
    write_json(output_dir / "input_audit.json", input_audit.as_dict())
    write_json(output_dir / "provenance.json", provenance)
    oos_metrics = {
        "status": "PASS" if oos_pass else "INSUFFICIENT",
        "passed": bool(oos_pass),
        "observations": int(effective),
        "effective_observations": int(effective),
        "raw_trades": int(raw_trades),
        "minimum_effective_observations": int(min_effective),
        "minimum_raw_trades": int(min_raw),
        "net_edge_bps": expectancy * 10_000.0 if np.isfinite(expectancy) else None,
        "expectancy_bps": expectancy * 10_000.0 if np.isfinite(expectancy) else None,
        "profit_factor": pf if np.isfinite(pf) else ("inf" if math.isinf(pf) else None),
        "folds": int(observations["fold"].nunique()) if not observations.empty else 0,
        "selection_rule": provenance.get("selection_rule") or provenance.get("selection_protocol"),
        "provenance_hash": provenance["provenance_hash"],
        "overlap_adjustment": "TEMPORAL_INTERVAL_CLUSTER_COUNT",
        "execution_authority": "NONE",
    }
    oos_evidence_path = output_dir / "oos_evidence.json"
    write_json(oos_evidence_path, oos_metrics)
    oos_reasons: list[str] = []
    if raw_trades < min_raw:
        oos_reasons.append("INSUFFICIENT_RAW_OOS_TRADES")
    if effective < min_effective:
        oos_reasons.append("INSUFFICIENT_EFFECTIVE_OOS_OBSERVATIONS")
    if not (np.isfinite(expectancy) and expectancy > 0):
        oos_reasons.append("NONPOSITIVE_OOS_NET_EXPECTANCY")
    oos_result = OOSProductionResultV2393(
        entity_id=entity_id,
        status="QUALIFIED" if oos_pass else "INSUFFICIENT",
        raw_trades=raw_trades,
        effective_observations=effective,
        folds=int(observations["fold"].nunique()) if not observations.empty else 0,
        net_expectancy_bps=expectancy * 10_000.0 if np.isfinite(expectancy) else None,
        profit_factor=pf if np.isfinite(pf) else None,
        passed=oos_pass,
        observations_path=str(obs_path),
        evidence_path=str(oos_evidence_path),
        provenance_hash=provenance["provenance_hash"],
        reasons=tuple(oos_reasons),
    )

    cost_result, cost_rows = produce_cost_stress_from_oos(
        observations,
        entity_id=entity_id,
        base_cost_bps_per_side=base_cost,
        effective_observations=effective,
        minimum_effective_observations=min_effective,
        output_dir=output_dir,
        config=production_cfg["cost_stress"],
        provenance_hash=provenance["provenance_hash"],
    )
    evidence_as_of = (
        pd.to_datetime(observations["exit_time"], utc=True).max().isoformat()
        if not observations.empty else datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    ingest = ingest_produced_evidence(
        store,
        entity_id=entity_id,
        oos_metrics=oos_metrics,
        cost_rows=cost_rows,
        oos_source_ref=f"v2393:{provenance['provenance_hash']}:oos",
        cost_source_prefix=f"v2393:{provenance['provenance_hash']}",
        as_of=evidence_as_of,
    )
    after = _assessment(store, entity_id, continuous_cfg)
    status = "PRODUCED_QUALIFIED" if oos_result.passed and cost_result.required_multiplier_passed else "PRODUCED_INSUFFICIENT"
    result = EvidenceProductionResultV2393(
        entity_id=entity_id,
        status=status,
        input_audit=input_audit.as_dict(),
        oos=oos_result.as_dict(),
        cost_stress=cost_result.as_dict(),
        evidence_added=int(ingest["added"]),
        before_assessment=before,
        after_assessment=after,
        output_dir=str(output_dir),
    )
    write_json(output_dir / "production_result.json", result.as_dict())
    return result


def produce_entity_evidence(
    project_root: Path,
    store: ResearchStoreV239,
    entity_id: str,
    *,
    production_cfg: dict,
    continuous_cfg: dict,
) -> EvidenceProductionResultV2393:
    before = _assessment(store, entity_id, continuous_cfg) if store.get_entity(entity_id) else None
    audit = audit_entity_inputs(project_root, store, entity_id, production_cfg=production_cfg)
    _, _, output_root = runtime_paths(project_root, production_cfg, continuous_cfg)
    safe_id = entity_id.replace(":", "__").replace("/", "_")
    output_dir = output_root / safe_id
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "input_audit.json", audit.as_dict())
    if not audit.ready:
        result = EvidenceProductionResultV2393(entity_id, "BLOCKED_INPUTS", audit.as_dict(), None, None, 0, before, before, str(output_dir))
        write_json(output_dir / "production_result.json", result.as_dict())
        return result
    entity = store.get_entity(entity_id)
    observations, provenance = replay_factory_oos(project_root, entity, config=production_cfg["factory_1h"])
    return _produce_observation_evidence(
        project_root, store, entity_id,
        observations=observations, provenance=provenance, input_audit=audit,
        production_cfg=production_cfg, continuous_cfg=continuous_cfg, before=before,
    )


def produce_external_observation_evidence(
    project_root: Path,
    store: ResearchStoreV239,
    entity_id: str,
    *,
    observations_file: str | Path,
    provenance_file: str | Path,
    base_cost_bps_per_side: float,
    production_cfg: dict,
    continuous_cfg: dict,
) -> EvidenceProductionResultV2393:
    entity = store.get_entity(entity_id)
    if entity is None:
        raise KeyError(entity_id)
    if not entity_id.startswith("STRATEGY:"):
        raise ValueError("external observation production requires STRATEGY entity")
    hid = entity_id.split(":", 1)[1]
    observations, provenance = load_external_observations(observations_file, provenance_file, entity_hypothesis_id=hid)
    if not math.isfinite(float(base_cost_bps_per_side)) or float(base_cost_bps_per_side) < 0:
        raise ValueError("base_cost_bps_per_side must be finite and nonnegative")
    provenance["base_cost_bps_per_side"] = float(base_cost_bps_per_side)
    provenance["selection_rule"] = provenance["selection_protocol"]
    # Bind the cost contract into provenance identity.
    from .oos_observation_validation_v2_39_3 import stable_hash
    provenance["provenance_hash"] = stable_hash({k:v for k,v in provenance.items() if k != "provenance_hash"})
    audit = ProductionInputAuditV2393(
        entity_id=entity_id,
        adapter="EXTERNAL_OBSERVATION_GRADE_OOS",
        status="READY",
        ready=True,
        reasons=(),
        details={"observations_file": str(observations_file), "provenance_file": str(provenance_file), "selection_protocol": provenance["selection_protocol"]},
    )
    before = _assessment(store, entity_id, continuous_cfg)
    return _produce_observation_evidence(
        project_root, store, entity_id,
        observations=observations, provenance=provenance, input_audit=audit,
        production_cfg=production_cfg, continuous_cfg=continuous_cfg, before=before,
    )


def _foundation_ready(assessment: dict) -> bool:
    positives = set(assessment.get("positive_reasons", []))
    return {"VALIDATION_STATUS_VALIDATED", "CROSS_ENGINE_VALIDATED", "DYNAMIC_UNIVERSE_GENERALIZED"}.issubset(positives)


def evidence_production_plan(
    project_root: Path,
    store: ResearchStoreV239,
    *,
    production_cfg: dict,
    continuous_cfg: dict,
    max_entities: int = 20,
) -> list[dict]:
    rows=[]
    for entity in store.list_entities(active_only=True):
        if entity.get("entity_type") != "STRATEGY":
            continue
        assessment=_assessment(store,entity["entity_id"],continuous_cfg)
        audit=audit_entity_inputs(project_root,store,entity["entity_id"],production_cfg=production_cfg)
        rows.append({
            "entity_id":entity["entity_id"],"role":entity.get("role"),"health":assessment.get("health"),
            "quality_score":assessment.get("quality_score"),"promotion_readiness_score":assessment.get("promotion_readiness_score"),
            "foundation_ready":_foundation_ready(assessment),"missing_requirements":assessment.get("missing_requirements",[]),
            "factory_adapter_ready":audit.ready,"adapter_status":audit.status,"adapter_reasons":list(audit.reasons),
            "external_observation_adapter_available":True,
            "selected_folds":audit.details.get("selected_folds",[]),"execution_authority":"NONE",
        })
    return sorted(rows,key=lambda x:(x["foundation_ready"],x["promotion_readiness_score"] or 0,x["quality_score"] or 0),reverse=True)[:max_entities]


def produce_due_evidence(
    project_root: Path,
    store: ResearchStoreV239,
    *,
    production_cfg: dict,
    continuous_cfg: dict,
    max_entities: int | None = None,
) -> dict:
    policy = production_cfg.get("produce_due", {})
    allowed_roles = set(policy.get("roles", ["CHALLENGER", "CANDIDATE"]))
    limit = int(max_entities or policy.get("max_entities", 10))
    candidates: list[tuple[float, str, dict]] = []
    skipped: list[dict] = []
    for entity in store.list_entities(active_only=True):
        if entity.get("role") not in allowed_roles:
            continue
        assessment = _assessment(store, entity["entity_id"], continuous_cfg)
        if assessment.get("gate_passed"):
            skipped.append({"entity_id": entity["entity_id"], "reason": "GATE_ALREADY_PASSED"})
            continue
        if policy.get("skip_quarantined", True) and assessment.get("health") == "QUARANTINED":
            skipped.append({"entity_id": entity["entity_id"], "reason": "QUARANTINED"})
            continue
        if policy.get("require_foundation_first", True) and not _foundation_ready(assessment):
            skipped.append({"entity_id": entity["entity_id"], "reason": "FOUNDATION_GATES_INCOMPLETE"})
            continue
        missing = set(assessment.get("missing_requirements", []))
        needs = (
            "NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE" in missing
            or any(x.startswith("NEED_POSITIVE_COST_STRESS_") for x in missing)
            or any(x.startswith("NEED_2_PROMOTION_EVIDENCE_SOURCE") for x in missing)
        )
        if not needs:
            skipped.append({"entity_id": entity["entity_id"], "reason": "NO_PRODUCIBLE_EVIDENCE_GAP"})
            continue
        candidates.append((float(assessment.get("promotion_readiness_score", 0.0)), entity["entity_id"], assessment))
    candidates.sort(reverse=True)
    results=[]
    for _,entity_id,_ in candidates[:limit]:
        try:
            results.append(produce_entity_evidence(project_root,store,entity_id,production_cfg=production_cfg,continuous_cfg=continuous_cfg).as_dict())
        except Exception as exc:
            results.append({"entity_id":entity_id,"status":"FAILED","error":f"{type(exc).__name__}: {exc}","execution_authority":"NONE"})
    _,_,output_root=runtime_paths(project_root,production_cfg,continuous_cfg)
    output_root.mkdir(parents=True,exist_ok=True)
    summary={
        "schema":"produce_due_summary_v2_39_3","generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "eligible":len(candidates),"attempted":len(results),
        "qualified":sum(r.get("status")=="PRODUCED_QUALIFIED" for r in results),
        "insufficient":sum(r.get("status")=="PRODUCED_INSUFFICIENT" for r in results),
        "blocked":sum(r.get("status")=="BLOCKED_INPUTS" for r in results),
        "failed":sum(r.get("status")=="FAILED" for r in results),
        "results":results,"skipped":skipped,
        "automatic_champion_promotion":False,"automatic_live_promotion":False,
        "broker_submission_enabled":False,"order_calls":0,"execution_authority":"NONE",
    }
    write_json(output_root/"latest_production_summary.json",summary)
    flat=[]
    for r in results:
        flat.append({
            "entity_id":r.get("entity_id"),"status":r.get("status"),"evidence_added":r.get("evidence_added",0),
            "before_quality":(r.get("before_assessment") or {}).get("quality_score"),"after_quality":(r.get("after_assessment") or {}).get("quality_score"),
            "before_readiness":(r.get("before_assessment") or {}).get("promotion_readiness_score"),"after_readiness":(r.get("after_assessment") or {}).get("promotion_readiness_score"),
            "gate_passed":(r.get("after_assessment") or {}).get("gate_passed"),"error":r.get("error"),
        })
    pd.DataFrame(flat).to_csv(output_root/"production_summary.csv",index=False)
    return summary


__all__ = [
    "load_production_config", "load_continuous_config", "runtime_paths", "audit_entity_inputs",
    "produce_entity_evidence", "produce_external_observation_evidence", "evidence_production_plan",
    "produce_due_evidence",
]
