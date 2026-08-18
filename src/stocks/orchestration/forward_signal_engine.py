from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.orchestration.strategy_forward_signals import (
    build_forward_trigger_map,
    research_entry_ready,
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
    }


def build_forward_signal_state(
    project_root: str | Path,
    *,
    strategy_registry: pd.DataFrame | None = None,
    required_status_column: str = "roster_status",
    required_status: str = "BROADLY_VALIDATED_FINALIST",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()

    matrix_path = (
        root
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/matrix.csv"
    )

    if not matrix_path.is_file():
        return pd.DataFrame(), {
            "schema": "forward_signal_state_v2_8",
            "rows": 0,
            "reason": "CANDIDATE_STRATEGY_MATRIX_MISSING",
            "execution_authority": "NONE",
        }

    matrix = pd.read_csv(matrix_path)

    if matrix.empty:
        return pd.DataFrame(), {
            "schema": "forward_signal_state_v2_8",
            "rows": 0,
            "reason": "CANDIDATE_STRATEGY_MATRIX_EMPTY",
            "execution_authority": "NONE",
        }

    legacy_policy = json.loads(
        (
            root
            / "config/final_decision_fabric_v2_7.json"
        ).read_text(encoding="utf-8")
    )["forward_signal"]

    recent_limit = int(legacy_policy["recent_entry_bars"])
    stale_limit = int(legacy_policy["maximum_stale_bars"])

    triggers = build_forward_trigger_map(
        root,
        matrix,
        strategy_registry=strategy_registry,
        required_status_column=required_status_column,
        required_status=required_status,
    )

    deployed_status: dict[str, str] = {}
    if strategy_registry is not None:
        deployed_status = {
            str(row["hypothesis_id"]): str(
                row.get(required_status_column) or ""
            )
            for row in strategy_registry.to_dict(orient="records")
        }

    rows: list[dict[str, Any]] = []

    for row in matrix.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        hypothesis_id = str(row["hypothesis_id"])
        source_state = str(
            row.get("setup_state")
            or "NO_SIGNAL_HISTORY"
        )

        raw_bars = row.get("bars_since_entry")
        try:
            bars = int(float(raw_bars))
        except (TypeError, ValueError):
            bars = None

        local_positive = _bool(
            row.get("local_evidence_positive", False)
        )

        trigger = triggers.get(
            (symbol, hypothesis_id),
            {
                "ready": False,
                "reason": "FORWARD_TRIGGER_NOT_EVALUATED",
            },
        )

        new_entry_ready = research_entry_ready(
            local_evidence_positive=local_positive,
            source_setup_state=source_state,
            trigger_ready=_bool(trigger.get("ready", False)),
        )

        if new_entry_ready:
            forward_state = "FRESH_CLOSED_BAR_ENTRY_TRIGGER"
        elif not local_positive:
            forward_state = "NO_ACTION_NEGATIVE_LOCAL_EVIDENCE"
        elif source_state == "ACTIVE_AT_DATA_BOUNDARY":
            forward_state = "ACTIVE_RESEARCH_POSITION_STATE"
        elif (
            source_state == "RECENT_ENTRY"
            and bars is not None
            and bars <= recent_limit
        ):
            forward_state = "RECENT_ENTRY_OBSERVE"
        elif bars is not None and bars > stale_limit:
            forward_state = "STALE"
        else:
            forward_state = "NO_FRESH_ENTRY"

        rows.append(
            {
                "symbol": symbol,
                "hypothesis_id": hypothesis_id,
                "strategy": row["strategy"],
                "validated_deployment_status": deployed_status.get(
                    hypothesis_id,
                    "LEGACY_ROSTER_PATH"
                    if strategy_registry is None
                    else "NOT_DEPLOYED",
                ),
                "family": row["family"],
                "research_lane": row.get("research_lane"),
                "shariah_gate": row.get("shariah_gate"),
                "contextual_score": row.get("contextual_score"),
                "applicability_score": row.get("applicability_score"),
                "local_evidence_positive": local_positive,
                "research_opportunity": _bool(
                    row.get("research_opportunity", False)
                ),
                "source_setup_state": source_state,
                "bars_since_entry": bars,
                "forward_state": forward_state,
                "new_entry_ready": new_entry_ready,
                "fresh_trigger_reason": trigger.get("reason"),
                "signal_bar_time": trigger.get("signal_bar_time"),
                "trigger_details_json": json.dumps(
                    trigger,
                    sort_keys=True,
                    default=str,
                ),
                "position_management_candidate": (
                    forward_state
                    == "ACTIVE_RESEARCH_POSITION_STATE"
                ),
                "requires_broker_flat_confirmation": True,
                "broker_flat_confirmation": False,
                "execution_contract": trigger.get(
                    "execution_contract",
                    row.get("execution_contract"),
                ),
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            }
        )

    frame = pd.DataFrame(rows).sort_values(
        [
            "new_entry_ready",
            "applicability_score",
        ],
        ascending=[
            False,
            False,
        ],
    )

    audit = {
        "schema": "forward_signal_state_v2_8",
        "rows": len(frame),
        "new_entry_ready": int(
            frame["new_entry_ready"].sum()
        ),
        "active_research_positions": int(
            frame["position_management_candidate"].sum()
        ),
        "recent_observe": int(
            (
                frame["forward_state"]
                == "RECENT_ENTRY_OBSERVE"
            ).sum()
        ),
        "forced_boundary_promoted_to_new_entry": int(
            (
                frame["new_entry_ready"]
                & (
                    frame["source_setup_state"]
                    == "ACTIVE_AT_DATA_BOUNDARY"
                )
            ).sum()
        ),
        "broker_flat_confirmations": 0,
        "closed_bars_only": True,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }

    return frame, audit
