from __future__ import annotations

from pathlib import Path

from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.store_v2_39 import ResearchStoreV239


def research_db_path_v240(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / "artifacts/research_runtime/continuous_quant_research_v2_39/research.db"


def register_rl_training_evidence_v240(project_root: str | Path, result: dict) -> bool:
    db = research_db_path_v240(project_root)
    if not db.is_file():
        return False
    store = ResearchStoreV239(db)
    entity_id = f"RL:{result['agent_id']}"
    if store.get_entity(entity_id) is None:
        store.upsert_entity(EntityV239(entity_id=entity_id, entity_type="RL_POLICY", family=result["algorithm"], source="AUTONOMOUS_LEARNING_V2_40"))
    test = dict(result.get("test") or {})
    metrics = {
        "net_return": float(test.get("total_return", 0.0)),
        "sharpe": float(test.get("sharpe", 0.0)),
        "max_drawdown": float(test.get("max_drawdown", 1.0)),
        "observations": int(test.get("steps", 0)),
        "trades": int(test.get("trades", 0)),
        "algorithm": result["algorithm"],
        "warm_started": bool(result.get("warm_started")),
        "passed": False,
        "status": "EVALUATED_CHALLENGER",
        "execution_authority": "NONE",
    }
    evidence = EvidenceRecordV239(
        entity_id=entity_id,
        evidence_type="RL_OOS",
        as_of=result.get("latest_data_time") or "1970-01-01T00:00:00+00:00",
        sample_count=int(test.get("steps", 0)),
        metrics=metrics,
        source="AUTONOMOUS_LEARNING_V2_40",
        source_ref=f"{result['agent_id']}:{result.get('latest_data_time')}",
    )
    return store.add_evidence(evidence)


def shadow_outcome_count_v240(project_root: str | Path, *, since: str | None = None) -> int:
    db = research_db_path_v240(project_root)
    if not db.is_file():
        return 0
    store = ResearchStoreV239(db)
    count = 0
    for entity in store.list_entities(active_only=False):
        for record in store.evidence_for(entity["entity_id"]):
            if record.get("evidence_type") != "SHADOW_TRADE":
                continue
            if since and str(record.get("as_of") or "") <= str(since):
                continue
            count += 1
    return count


def maximum_drift_severity_v240(project_root: str | Path) -> float:
    db = research_db_path_v240(project_root)
    if not db.is_file():
        return 0.0
    store = ResearchStoreV239(db)
    worst = 0.0
    for entity in store.list_entities(active_only=False):
        drift = [r for r in store.evidence_for(entity["entity_id"]) if r.get("evidence_type") == "DRIFT"]
        if not drift:
            continue
        latest = max(drift, key=lambda r: str(r.get("as_of") or ""))
        m = latest.get("metrics") or {}
        worst = max(worst, float(m.get("psi_max") or 0.0), float(m.get("js_max") or 0.0))
    return min(1.0, worst)


__all__ = [
    "register_rl_training_evidence_v240",
    "shadow_outcome_count_v240",
    "maximum_drift_severity_v240",
    "research_db_path_v240",
]
