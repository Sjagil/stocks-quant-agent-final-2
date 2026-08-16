
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_forward_signal_state(
    project_root: str | Path,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    root = Path(
        project_root
    ).resolve()

    matrix_path = (
        root
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/matrix.csv"
    )

    if not matrix_path.is_file():
        return (
            pd.DataFrame(),
            {
                "schema": (
                    "forward_signal_state_v2_7"
                ),
                "rows": 0,
                "reason": (
                    "CANDIDATE_STRATEGY_"
                    "MATRIX_MISSING"
                ),
                "execution_authority": (
                    "NONE"
                ),
            },
        )

    matrix = pd.read_csv(
        matrix_path
    )

    if matrix.empty:
        return (
            pd.DataFrame(),
            {
                "schema": (
                    "forward_signal_state_v2_7"
                ),
                "rows": 0,
                "reason": (
                    "CANDIDATE_STRATEGY_"
                    "MATRIX_EMPTY"
                ),
                "execution_authority": (
                    "NONE"
                ),
            },
        )

    policy = json.loads(
        (
            root
            / "config/"
            "final_decision_fabric_v2_7.json"
        ).read_text(
            encoding="utf-8"
        )
    )[
        "forward_signal"
    ]

    recent_limit = int(
        policy[
            "recent_entry_bars"
        ]
    )

    stale_limit = int(
        policy[
            "maximum_stale_bars"
        ]
    )

    rows: list[
        dict[str, Any]
    ] = []

    for row in matrix.to_dict(
        orient="records"
    ):
        source_state = str(
            row.get(
                "setup_state"
            )
            or "NO_SIGNAL_HISTORY"
        )

        raw_bars = row.get(
            "bars_since_entry"
        )

        try:
            bars = int(
                float(
                    raw_bars
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            bars = None

        local_positive = bool(
            row.get(
                "local_evidence_positive",
                False,
            )
        )

        if not local_positive:
            forward_state = (
                "NO_ACTION_NEGATIVE_"
                "LOCAL_EVIDENCE"
            )

        elif source_state == (
            "ACTIVE_AT_DATA_BOUNDARY"
        ):
            # A forced backtest end describes position state, not a fresh
            # entry trigger. Never promote it to a broker entry.
            forward_state = (
                "ACTIVE_RESEARCH_"
                "POSITION_STATE"
            )

        elif (
            source_state
            == "RECENT_ENTRY"
            and bars is not None
            and bars <= recent_limit
        ):
            # This is useful observation evidence but still not a fresh signal:
            # the entry happened in historical/replay evaluation.
            forward_state = (
                "RECENT_ENTRY_OBSERVE"
            )

        elif (
            bars is not None
            and bars > stale_limit
        ):
            forward_state = (
                "STALE"
            )

        else:
            forward_state = (
                "NO_FRESH_ENTRY"
            )

        rows.append(
            {
                "symbol": str(
                    row["symbol"]
                ).upper(),
                "hypothesis_id": (
                    row[
                        "hypothesis_id"
                    ]
                ),
                "strategy": (
                    row["strategy"]
                ),
                "family": (
                    row["family"]
                ),
                "research_lane": (
                    row.get(
                        "research_lane"
                    )
                ),
                "shariah_gate": (
                    row.get(
                        "shariah_gate"
                    )
                ),
                "contextual_score": (
                    row.get(
                        "contextual_score"
                    )
                ),
                "applicability_score": (
                    row.get(
                        "applicability_score"
                    )
                ),
                "local_evidence_positive": (
                    local_positive
                ),
                "research_opportunity": bool(
                    row.get(
                        "research_opportunity",
                        False,
                    )
                ),
                "source_setup_state": (
                    source_state
                ),
                "bars_since_entry": (
                    bars
                ),
                "forward_state": (
                    forward_state
                ),
                # Deliberately false until a strategy-specific closed-bar
                # trigger adapter proves a new signal exists after the latest
                # canonical bar.
                "new_entry_ready": False,
                "position_management_candidate": (
                    forward_state
                    == (
                        "ACTIVE_RESEARCH_"
                        "POSITION_STATE"
                    )
                ),
                "requires_strategy_specific_closed_bar_trigger": (
                    True
                ),
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
                "order_calls": 0,
            }
        )

    frame = pd.DataFrame(
        rows
    ).sort_values(
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
        "schema": (
            "forward_signal_state_v2_7"
        ),
        "rows": int(
            len(frame)
        ),
        "new_entry_ready": int(
            frame[
                "new_entry_ready"
            ].sum()
        ),
        "active_research_positions": int(
            frame[
                "position_management_candidate"
            ].sum()
        ),
        "recent_observe": int(
            (
                frame[
                    "forward_state"
                ]
                == "RECENT_ENTRY_OBSERVE"
            ).sum()
        ),
        "forced_boundary_promoted_to_new_entry": 0,
        "closed_bars_only": True,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "order_calls": 0,
    }

    return (
        frame,
        audit,
    )
