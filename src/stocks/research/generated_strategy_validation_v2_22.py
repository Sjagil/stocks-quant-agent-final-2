from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "generated_strategy_validation_audit_v2_22_2"
OUTPUT_ROOT = Path(
    "artifacts/research_runtime/generated_strategy_validation_v2_22"
)

TERMINAL_CROSS_ENGINE_STATUSES = {
    "CROSS_ENGINE_VALIDATED",
    "CROSS_ENGINE_NOT_VALIDATED",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"hypothesis_id": str})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _records(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame.empty or "hypothesis_id" not in frame:
        return {}
    normalized = frame.copy()
    normalized["hypothesis_id"] = normalized["hypothesis_id"].astype(str)
    if normalized["hypothesis_id"].duplicated().any():
        duplicates = sorted(
            normalized.loc[
                normalized["hypothesis_id"].duplicated(keep=False),
                "hypothesis_id",
            ].unique()
        )
        raise ValueError(f"duplicate pipeline hypothesis ids: {duplicates}")
    return {
        str(row["hypothesis_id"]): row
        for row in normalized.to_dict(orient="records")
    }


def _generalization_is_terminal(status: str, cross_status: str) -> bool:
    if cross_status == "CROSS_ENGINE_NOT_VALIDATED":
        return status == "WAITING_CROSS_ENGINE"
    return (
        status in {
            "DYNAMIC_UNIVERSE_VALIDATED",
            "DYNAMIC_UNIVERSE_REJECT",
        }
        or status.startswith("NOT_EVALUABLE_")
    )


def build_generated_strategy_validation_audit(
    project_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    generated_root = (
        root / "artifacts/research_runtime/strategy_generation_v2_22"
    )
    queue = _read_csv(generated_root / "validation_queue.csv")
    cross_engine = _read_csv(
        generated_root / "cross_engine/strategy_summary.csv"
    )
    generalization = _read_csv(
        root
        / "artifacts/research_runtime/dynamic_universe_generalization/summary.csv"
    )
    registry = _read_csv(
        root / "artifacts/research_runtime/research_candidate_registry/registry.csv"
    )
    roster = _read_csv(
        root / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )

    cross_by_id = _records(cross_engine)
    generalization_by_id = _records(generalization)
    registry_by_id = _records(registry)
    roster_by_id = _records(roster)

    rows: list[dict[str, Any]] = []
    global_errors: list[str] = []
    if queue.empty:
        global_errors.append("VALIDATION_QUEUE_EMPTY")
    elif "hypothesis_id" not in queue:
        global_errors.append("VALIDATION_QUEUE_SCHEMA_INVALID")
    elif queue["hypothesis_id"].astype(str).duplicated().any():
        global_errors.append("VALIDATION_QUEUE_DUPLICATES")

    if not global_errors:
        for queue_row in queue.to_dict(orient="records"):
            hypothesis_id = str(queue_row["hypothesis_id"])
            cross_row = cross_by_id.get(hypothesis_id, {})
            general_row = generalization_by_id.get(hypothesis_id, {})
            registry_row = registry_by_id.get(hypothesis_id, {})
            roster_row = roster_by_id.get(hypothesis_id, {})

            cross_status = str(cross_row.get("status") or "MISSING")
            general_status = str(
                general_row.get("generalization_status") or "MISSING"
            )
            promotion_stage = str(
                registry_row.get("promotion_stage") or "MISSING"
            )
            roster_status = str(roster_row.get("roster_status") or "MISSING")

            errors: list[str] = []
            if cross_status not in TERMINAL_CROSS_ENGINE_STATUSES:
                errors.append("CROSS_ENGINE_EVIDENCE_INCOMPLETE")
            if not _generalization_is_terminal(general_status, cross_status):
                errors.append("GENERALIZATION_EVIDENCE_INCOMPLETE")
            if not registry_row:
                errors.append("REGISTRY_ROW_MISSING")
            if not roster_row:
                errors.append("ROSTER_ROW_MISSING")

            if roster_status == "BROADLY_VALIDATED_FINALIST":
                pipeline_status = "BROADLY_VALIDATED_FINALIST"
            elif cross_status == "CROSS_ENGINE_NOT_VALIDATED":
                pipeline_status = "REJECTED_CROSS_ENGINE"
            elif general_status == "DYNAMIC_UNIVERSE_REJECT":
                pipeline_status = "REJECTED_GENERALIZATION"
            elif general_status.startswith("NOT_EVALUABLE_"):
                pipeline_status = "BLOCKED_GENERALIZATION_DATA"
            elif roster_status == "REDUNDANT_ALTERNATE":
                pipeline_status = "REDUNDANT_ALTERNATE"
            elif errors:
                pipeline_status = "PIPELINE_INCOMPLETE"
            else:
                pipeline_status = "RESEARCH_COMPLETE_NOT_PROMOTED"

            rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "strategy": str(queue_row.get("strategy") or ""),
                    "family": str(queue_row.get("family") or ""),
                    "cross_engine_status": cross_status,
                    "generalization_status": general_status,
                    "promotion_stage": promotion_stage,
                    "roster_status": roster_status,
                    "pipeline_status": pipeline_status,
                    "evidence_complete": not errors,
                    "errors": "|".join(errors),
                    "execution_authority": "NONE",
                }
            )

    frame = pd.DataFrame(rows)
    incomplete = (
        int((~frame["evidence_complete"].astype(bool)).sum())
        if not frame.empty
        else 0
    )
    broad_finalists = (
        int(
            (
                frame["pipeline_status"] == "BROADLY_VALIDATED_FINALIST"
            ).sum()
        )
        if not frame.empty
        else 0
    )
    pipeline_complete = bool(
        not global_errors and not frame.empty and incomplete == 0
    )
    audit = {
        "schema": SCHEMA,
        "pipeline_complete": pipeline_complete,
        "queued_strategies": len(queue),
        "audited_strategies": len(frame),
        "incomplete_strategies": incomplete,
        "broadly_validated_finalists": broad_finalists,
        "blocked_generalization_data": int(
            (
                frame.get("pipeline_status", pd.Series(dtype=str))
                == "BLOCKED_GENERALIZATION_DATA"
            ).sum()
        ),
        "cross_engine_rejects": int(
            (
                frame.get("pipeline_status", pd.Series(dtype=str))
                == "REJECTED_CROSS_ENGINE"
            ).sum()
        ),
        "generalization_rejects": int(
            (
                frame.get("pipeline_status", pd.Series(dtype=str))
                == "REJECTED_GENERALIZATION"
            ).sum()
        ),
        "errors": global_errors,
        "automatic_finalist_promotion": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    return frame, audit


def write_generated_strategy_validation_audit(
    project_root: str | Path,
    *,
    output_root: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], Path]:
    root = Path(project_root).resolve()
    frame, audit = build_generated_strategy_validation_audit(root)
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else root / OUTPUT_ROOT
    )
    destination.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination / "strategy_status.csv", index=False)
    (destination / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return frame, audit, destination


__all__ = [
    "SCHEMA",
    "build_generated_strategy_validation_audit",
    "write_generated_strategy_validation_audit",
]
