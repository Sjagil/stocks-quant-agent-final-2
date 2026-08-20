from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.orchestration.generated_strategy_forward_signals_v2_23 import (
    GENERATED_NEXT_OPEN_STRATEGIES,
)
from stocks.research.strategy_generation_v2_22 import blueprint_registry


SCHEMA = "generated_forward_adapter_audit_v2_23"
SOURCE_ENGINE = "strategy_generation_v2_22"
BROAD_STATUS = "BROADLY_VALIDATED_FINALIST"


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def _json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_generated_forward_adapter_audit(
    project_root: str | Path,
    *,
    require_runtime: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    catalog = sorted(blueprint.name for blueprint in blueprint_registry())
    supported = sorted(GENERATED_NEXT_OPEN_STRATEGIES)
    missing_catalog = sorted(set(catalog).difference(supported))
    unexpected_adapters = sorted(set(supported).difference(catalog))
    errors: list[str] = []

    roster_path = (
        root
        / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    )
    roster = _csv(roster_path)
    broad_generated = pd.DataFrame()
    missing_finalist_adapters: list[str] = []

    if not roster.empty:
        required = {
            "hypothesis_id",
            "strategy",
            "source_engine",
            "roster_status",
        }
        missing_columns = sorted(required.difference(roster.columns))
        if missing_columns:
            errors.append(
                "ROSTER_MISSING_COLUMNS:" + ",".join(missing_columns)
            )
        else:
            broad_generated = roster.loc[
                (roster["source_engine"].astype(str) == SOURCE_ENGINE)
                & (roster["roster_status"].astype(str) == BROAD_STATUS)
            ].copy()
            missing_finalist_adapters = sorted(
                set(broad_generated["strategy"].astype(str)).difference(
                    GENERATED_NEXT_OPEN_STRATEGIES
                )
            )

    runtime_errors: list[str] = []
    matrix_missing_ids: list[str] = []
    signal_missing_ids: list[str] = []
    not_implemented_rows = 0

    if require_runtime:
        if broad_generated.empty:
            runtime_errors.append("NO_BROAD_GENERATED_FINALISTS")

        matrix = _csv(
            root
            / "artifacts/research_runtime/candidate_strategy_matrix/matrix.csv"
        )
        signals = _csv(
            root
            / "artifacts/research_runtime/forward_signal_state/signals.csv"
        )
        forward_audit = _json(
            root
            / "artifacts/research_runtime/forward_signal_state/audit.json"
        )

        if matrix.empty:
            runtime_errors.append("CANDIDATE_STRATEGY_MATRIX_MISSING_OR_EMPTY")
        if signals.empty:
            runtime_errors.append("FORWARD_SIGNAL_STATE_MISSING_OR_EMPTY")

        finalist_ids = set(
            broad_generated.get(
                "hypothesis_id", pd.Series(dtype=str)
            ).astype(str)
        )
        if finalist_ids and not matrix.empty:
            matrix_ids = set(matrix["hypothesis_id"].astype(str))
            matrix_missing_ids = sorted(finalist_ids.difference(matrix_ids))
            if matrix_missing_ids:
                runtime_errors.append("GENERATED_FINALISTS_MISSING_FROM_MATRIX")

        if finalist_ids and not signals.empty:
            signal_ids = set(signals["hypothesis_id"].astype(str))
            signal_missing_ids = sorted(finalist_ids.difference(signal_ids))
            if signal_missing_ids:
                runtime_errors.append(
                    "GENERATED_FINALISTS_MISSING_FROM_FORWARD_STATE"
                )
            scoped = signals.loc[
                signals["hypothesis_id"].astype(str).isin(finalist_ids)
            ].copy()
            if "fresh_trigger_reason" in scoped.columns:
                reasons = scoped["fresh_trigger_reason"].fillna("").astype(str)
                not_implemented_rows = int(
                    reasons.str.contains("ADAPTER_NOT_IMPLEMENTED").sum()
                )
                if not_implemented_rows:
                    runtime_errors.append(
                        "GENERATED_FORWARD_ADAPTER_NOT_IMPLEMENTED_AT_RUNTIME"
                    )

        if forward_audit:
            if str(forward_audit.get("execution_authority")) != "NONE":
                runtime_errors.append("FORWARD_EXECUTION_AUTHORITY_NOT_NONE")
            if int(forward_audit.get("broker_calls", 0)) != 0:
                runtime_errors.append("FORWARD_BROKER_CALLS_NONZERO")
            if int(forward_audit.get("order_calls", 0)) != 0:
                runtime_errors.append("FORWARD_ORDER_CALLS_NONZERO")

    coverage_complete = not (
        missing_catalog
        or unexpected_adapters
        or missing_finalist_adapters
        or errors
        or runtime_errors
    )

    return {
        "schema": SCHEMA,
        "catalog_strategies": catalog,
        "supported_generated_strategies": supported,
        "catalog_strategy_count": len(catalog),
        "supported_generated_strategy_count": len(supported),
        "missing_catalog_adapters": missing_catalog,
        "unexpected_generated_adapters": unexpected_adapters,
        "roster_present": roster_path.is_file(),
        "broad_generated_finalists": int(len(broad_generated)),
        "broad_generated_finalist_ids": sorted(
            broad_generated.get(
                "hypothesis_id", pd.Series(dtype=str)
            ).astype(str).tolist()
        ),
        "missing_finalist_adapters": missing_finalist_adapters,
        "runtime_required": bool(require_runtime),
        "matrix_missing_finalist_ids": matrix_missing_ids,
        "forward_state_missing_finalist_ids": signal_missing_ids,
        "runtime_not_implemented_rows": not_implemented_rows,
        "errors": errors,
        "runtime_errors": runtime_errors,
        "coverage_complete": bool(coverage_complete),
        "automatic_finalist_promotion": False,
        "automatic_live_promotion": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def write_generated_forward_adapter_audit(
    project_root: str | Path,
    *,
    require_runtime: bool = False,
) -> tuple[dict[str, Any], Path]:
    root = Path(project_root).resolve()
    payload = build_generated_forward_adapter_audit(
        root,
        require_runtime=require_runtime,
    )
    output = (
        root
        / "artifacts/research_runtime/generated_forward_adapter_audit_v2_23"
    )
    output.mkdir(parents=True, exist_ok=True)
    path = output / "audit.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return payload, path


__all__ = [
    "build_generated_forward_adapter_audit",
    "write_generated_forward_adapter_audit",
]
