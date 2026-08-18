from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.research.validation_policy import promotion_from_evidence

SURVIVOR_STATUSES = {"SURVIVOR", "PROVISIONAL_SURVIVOR", "STRONG_SURVIVOR"}


def _read_optional_csv(path: Path) -> pd.DataFrame:
    # Read a research artifact without treating zero rows as an error.
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()



def _records(path: Path, key: str = "hypothesis_id") -> dict[str, dict]:
    if not path.is_file():
        return {}
    frame = pd.read_csv(path)
    if frame.empty or key not in frame.columns:
        return {}
    return {str(row[key]): row for row in frame.to_dict(orient="records")}


def build_research_candidate_registry(project_root: Path) -> tuple[pd.DataFrame, dict]:
    from stocks.research.validated_strategy_registry import write_validated_strategy_registry

    validated, validated_audit, validated_path = write_validated_strategy_registry(project_root)
    indicator_path = project_root / "artifacts/research_runtime/indicator_discovery_1h/survivors.csv"
    indicator_cross_path = project_root / "artifacts/research_runtime/indicator_pybroker_crosscheck/summary.csv"
    generalization_path = project_root / "artifacts/research_runtime/dynamic_universe_generalization/summary.csv"
    mtf_path = project_root / "artifacts/research_runtime/multitimeframe_strategy_research_v2_15_1/survivors.csv"
    kronos_path = project_root / "artifacts/research_runtime/kronos_strategy_research_v2_15/survivors.csv"

    indicator_cross = _records(indicator_cross_path)
    generalization = _records(generalization_path)
    rows: list[dict] = []

    for _, item in validated.iterrows():
        hypothesis_id = str(item["hypothesis_id"])
        general = generalization.get(hypothesis_id, {})
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "strategy": item["strategy"],
                "family": item["family"],
                "params_json": item["params_json"],
                "source_engine": "strategy_factory_1h",
                "research_status": item["factory_status"],
                "validation_status": item["validation_status"],
                "promotion_stage": item["promotion_stage"],
                "validation_route": item["validation_engine"],
                "execution_contract": item.get("execution_contract", "UNKNOWN"),
                "cross_engine_status": item.get("evidence_status", item["validation_status"]),
                "cross_engine_validated": item["validation_status"] == "VALIDATED",
                "generalization_status": general.get("generalization_status", "PENDING"),
                "generalization_reasons": general.get("generalization_reasons", ""),
                "dynamic_universe_generalized": general.get("generalization_status") == "DYNAMIC_UNIVERSE_VALIDATED",
                "execution_authority": "NONE",
            }
        )

    if indicator_path.is_file():
        indicator = pd.read_csv(indicator_path)
        for _, item in indicator.iterrows():
            if str(item.get("status")) not in SURVIVOR_STATUSES:
                continue
            hypothesis_id = str(item["hypothesis_id"])
            cross = indicator_cross.get(hypothesis_id, {})
            general = generalization.get(hypothesis_id, {})
            cross_status = str(cross.get("crosscheck_status") or "PENDING")
            general_status = str(general.get("generalization_status") or "PENDING")
            stage = promotion_from_evidence(
                existing_stage="VALIDATION_QUEUE",
                crosscheck_status=cross_status,
                generalization_status=general_status,
            )
            rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "strategy": item["template"],
                    "family": item["family"],
                    "params_json": item["params_json"],
                    "source_engine": item.get("source_engine", "indicator_discovery_v1"),
                    "research_status": item["status"],
                    "validation_status": (
                        "VALIDATED" if cross_status == "CROSS_ENGINE_VALIDATED"
                        else "PROVISIONAL" if cross_status == "CROSS_ENGINE_PROVISIONAL"
                        else "REJECTED" if cross_status == "CROSS_ENGINE_REJECT"
                        else "PENDING"
                    ),
                    "promotion_stage": stage,
                    "validation_route": item.get("validation_route", "PYBROKER_CROSS_ENGINE_REQUIRED"),
                    "execution_contract": item.get("execution_contract", "NEXT_OPEN_REPLAY"),
                    "cross_engine_status": cross_status,
                    "cross_engine_validated": cross_status == "CROSS_ENGINE_VALIDATED",
                    "generalization_status": general_status,
                    "generalization_reasons": general.get("generalization_reasons", ""),
                    "dynamic_universe_generalized": general_status == "DYNAMIC_UNIVERSE_VALIDATED",
                    "execution_authority": "NONE",
                }
            )

    if kronos_path.is_file():
        kronos = _read_optional_csv(kronos_path)
        for _, item in kronos.iterrows():
            if str(item.get("status")) not in SURVIVOR_STATUSES:
                continue
            rows.append(
                {
                    "hypothesis_id": str(item["hypothesis_id"]),
                    "strategy": item.get("template", item.get("strategy")),
                    "family": item["family"],
                    "params_json": item["params_json"],
                    "source_engine": "kronos_foundation_model_v2_15",
                    "research_status": item["status"],
                    "validation_status": "PENDING",
                    "promotion_stage": "VALIDATION_QUEUE",
                    "validation_route": item.get(
                        "validation_route",
                        "KRONOS_CROSS_ENGINE_AND_DYNAMIC_GENERALIZATION_REQUIRED",
                    ),
                    "execution_contract": item.get(
                        "execution_contract",
                        "NEXT_OPEN_TO_HORIZON_CLOSE",
                    ),
                    "cross_engine_status": "PENDING",
                    "cross_engine_validated": False,
                    "generalization_status": "PENDING",
                    "generalization_reasons": "",
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )

    if mtf_path.is_file():
        mtf = _read_optional_csv(mtf_path)
        for _, item in mtf.iterrows():
            if str(item.get("status")) not in SURVIVOR_STATUSES:
                continue
            rows.append(
                {
                    "hypothesis_id": str(item["hypothesis_id"]),
                    "strategy": item.get("template", item.get("strategy")),
                    "family": item["family"],
                    "params_json": item["params_json"],
                    "source_engine": "multitimeframe_strategy_factory_v2_15_1",
                    "research_status": item["status"],
                    "validation_status": "PENDING",
                    "promotion_stage": "VALIDATION_QUEUE",
                    "validation_route": item.get(
                        "validation_route",
                        "MTF_CROSS_ENGINE_AND_DYNAMIC_GENERALIZATION_REQUIRED",
                    ),
                    "execution_contract": item.get(
                        "execution_contract",
                        "NEXT_15M_OPEN_FIXED_HORIZON",
                    ),
                    "cross_engine_status": "PENDING",
                    "cross_engine_validated": False,
                    "generalization_status": "PENDING",
                    "generalization_reasons": "",
                    "dynamic_universe_generalized": False,
                    "execution_authority": "NONE",
                }
            )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        if frame["hypothesis_id"].duplicated().any():
            duplicates = frame.loc[frame["hypothesis_id"].duplicated(keep=False), "hypothesis_id"].tolist()
            raise ValueError(f"duplicate research candidate hypothesis ids: {duplicates}")
        stage_rank = {
            "FINALIST_CANDIDATE": 0,
            "CHALLENGER": 1,
            "GENERALIZATION_QUEUE": 2,
            "VALIDATION_QUEUE": 3,
            "REJECTED_AFTER_GENERALIZATION": 8,
            "REJECTED_AFTER_CROSSCHECK": 9,
        }
        frame["_rank"] = frame["promotion_stage"].map(stage_rank).fillna(8)
        frame = frame.sort_values(["_rank", "family", "strategy", "hypothesis_id"]).drop(columns=["_rank"]).reset_index(drop=True)

    audit = {
        "schema": "research_candidate_registry_v2",
        "candidate_count": int(len(frame)),
        "finalist_count": int((frame["promotion_stage"] == "FINALIST_CANDIDATE").sum()) if not frame.empty else 0,
        "challenger_count": int((frame["promotion_stage"] == "CHALLENGER").sum()) if not frame.empty else 0,
        "generalization_queue_count": int((frame["promotion_stage"] == "GENERALIZATION_QUEUE").sum()) if not frame.empty else 0,
        "validation_queue_count": int((frame["promotion_stage"] == "VALIDATION_QUEUE").sum()) if not frame.empty else 0,
        "rejected_after_generalization_count": int((frame["promotion_stage"] == "REJECTED_AFTER_GENERALIZATION").sum()) if not frame.empty else 0,
        "rejected_after_crosscheck_count": int((frame["promotion_stage"] == "REJECTED_AFTER_CROSSCHECK").sum()) if not frame.empty else 0,
        "cross_engine_validated_count": int(frame["cross_engine_validated"].fillna(False).astype(bool).sum()) if not frame.empty else 0,
        "dynamic_universe_generalized_count": int(frame["dynamic_universe_generalized"].fillna(False).astype(bool).sum()) if not frame.empty else 0,
        "validated_registry": str(validated_path),
        "validated_registry_live_ready": bool(validated_audit["live_ready"]),
        "indicator_survivors_present": indicator_path.is_file(),
        "indicator_crosscheck_present": indicator_cross_path.is_file(),
        "generalization_present": generalization_path.is_file(),
        "multitimeframe_survivors_present": mtf_path.is_file(),
        "kronos_survivors_present": kronos_path.is_file(),
        "automatic_live_promotion": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    return frame, audit


def write_research_candidate_registry(project_root: Path) -> tuple[pd.DataFrame, dict, Path]:
    frame, audit = build_research_candidate_registry(project_root)
    root = project_root / "artifacts/research_runtime/research_candidate_registry"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "registry.csv"
    frame.to_csv(path, index=False)
    (root / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return frame, audit, path
