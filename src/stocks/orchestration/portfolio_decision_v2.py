
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
    }


def build_portfolio_proposals(
    project_root: str | Path,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    root = Path(
        project_root
    ).resolve()

    signal_path = (
        root
        / "artifacts/research_runtime/"
        "forward_signal_state/signals.csv"
    )
    shariah_path = (
        root
        / "artifacts/research_runtime/"
        "shariah_financial_verification/"
        "verification.csv"
    )
    matrix_path = (
        root
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/"
        "matrix.csv"
    )

    if (
        not signal_path.is_file()
        or not matrix_path.is_file()
    ):
        return (
            pd.DataFrame(),
            {
                "schema": (
                    "portfolio_decision_v2_7"
                ),
                "proposal_count": 0,
                "reason": (
                    "FORWARD_SIGNAL_OR_"
                    "MATRIX_MISSING"
                ),
                "execution_authority": (
                    "NONE"
                ),
            },
        )

    signals = pd.read_csv(
        signal_path
    )

    matrix = pd.read_csv(
        matrix_path
    )

    shariah = (
        pd.read_csv(
            shariah_path
        )
        if shariah_path.is_file()
        else pd.DataFrame()
    )

    shariah_map = (
        {
            str(
                row["symbol"]
            ).upper(): row
            for row
            in shariah.to_dict(
                orient="records"
            )
        }
        if not shariah.empty
        else {}
    )

    policy = json.loads(
        (
            root
            / "config/"
            "final_decision_fabric_v2_7.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    portfolio = policy[
        "portfolio"
    ]

    canary = policy[
        "canary"
    ]

    joined = signals.merge(
        matrix[
            [
                "symbol",
                "hypothesis_id",
                "trailing_expectancy_bps",
                "trailing_stress_expectancy_bps",
                "trailing_profit_factor",
            ]
        ],
        on=[
            "symbol",
            "hypothesis_id",
        ],
        how="left",
    )

    rows: list[
        dict[str, Any]
    ] = []

    for symbol, group in (
        joined.groupby(
            "symbol"
        )
    ):
        sh = shariah_map.get(
            str(symbol).upper(),
            {},
        )

        verified = _boolean(
            sh.get(
                "trade_eligible",
                False,
            )
        )

        votes = int(
            group[
                "local_evidence_positive"
            ]
            .map(_boolean)
            .sum()
        )

        best_app = float(
            pd.to_numeric(
                group[
                    "applicability_score"
                ],
                errors="coerce",
            ).max()
        )

        avg_app = float(
            pd.to_numeric(
                group[
                    "applicability_score"
                ],
                errors="coerce",
            ).mean()
        )

        positive_expectancy = (
            pd.to_numeric(
                group[
                    "trailing_stress_expectancy_bps"
                ],
                errors="coerce",
            )
        )

        positive_expectancy = (
            positive_expectancy.loc[
                positive_expectancy
                > 0
            ]
        )

        conviction = max(
            0.0,
            min(
                1.0,
                (
                    0.55
                    * (
                        best_app
                        / 100.0
                    )
                    + 0.25
                    * (
                        avg_app
                        / 100.0
                    )
                    + 0.20
                    * min(
                        votes / 2.0,
                        1.0,
                    )
                ),
            ),
        )

        any_fresh_entry = bool(
            group[
                "new_entry_ready"
            ]
            .map(_boolean)
            .any()
        )

        active_state = bool(
            group[
                "position_management_candidate"
            ]
            .map(_boolean)
            .any()
        )

        blockers: list[str] = []

        if not verified:
            blockers.append(
                "SHARIAH_VERIFICATION_"
                "NOT_COMPLETE"
            )

        if votes < int(
            portfolio[
                "minimum_strategy_votes"
            ]
        ):
            blockers.append(
                "INSUFFICIENT_STRATEGY_VOTES"
            )

        if conviction < float(
            portfolio[
                "minimum_conviction"
            ]
        ):
            blockers.append(
                "CONVICTION_BELOW_MINIMUM"
            )

        if not any_fresh_entry:
            blockers.append(
                "NO_FRESH_CLOSED_BAR_"
                "ENTRY_TRIGGER"
            )

        if (
            any_fresh_entry
            and not blockers
        ):
            decision = (
                "BUY_NEW"
            )
        elif active_state:
            decision = (
                "OBSERVE_EXISTING_"
                "POSITION_STATE"
            )
        else:
            decision = "SKIP"

        rows.append(
            {
                "symbol": (
                    str(
                        symbol
                    ).upper()
                ),
                "decision": (
                    decision
                ),
                "conviction": (
                    conviction
                ),
                "strategy_votes": (
                    votes
                ),
                "strategy_ids": "|".join(
                    sorted(
                        set(
                            group[
                                "hypothesis_id"
                            ]
                            .dropna()
                            .astype(str)
                        )
                    )
                ),
                "strategy_families": "|".join(
                    sorted(
                        set(
                            group[
                                "family"
                            ]
                            .dropna()
                            .astype(str)
                        )
                    )
                ),
                "best_applicability_score": (
                    best_app
                ),
                "average_applicability_score": (
                    avg_app
                ),
                "median_positive_stress_expectancy_bps": (
                    float(
                        positive_expectancy
                        .median()
                    )
                    if not (
                        positive_expectancy
                        .empty
                    )
                    else None
                ),
                "shariah_status": (
                    sh.get(
                        "status",
                        "SHARIAH_DATA_INCOMPLETE",
                    )
                ),
                "shariah_verified": (
                    verified
                ),
                "fresh_entry_trigger": (
                    any_fresh_entry
                ),
                "active_position_state": (
                    active_state
                ),
                "canary_quantity_mode": (
                    canary[
                        "quantity_mode"
                    ]
                ),
                "fractional_shares_allowed": (
                    bool(
                        canary[
                            "fractional_shares_allowed"
                        ]
                    )
                ),
                "fixed_euro_order_cap_enabled": (
                    bool(
                        canary[
                            "fixed_euro_order_cap_enabled"
                        ]
                    )
                ),
                "maximum_order_eur": (
                    canary[
                        "maximum_order_eur"
                    ]
                ),
                "sizing_authority": (
                    canary[
                        "primary_sizing_authority"
                    ]
                ),
                # Quantity is intentionally unresolved here: it needs current
                # IBKR cash/equity, current holdings, price, stop distance and
                # portfolio heat. v2.8 will bind these to broker state.
                "requested_quantity": None,
                "whole_share_quantity": None,
                "blockers": "|".join(
                    blockers
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
    )

    if not frame.empty:
        rank = {
            "BUY_NEW": 0,
            (
                "OBSERVE_EXISTING_"
                "POSITION_STATE"
            ): 1,
            "SKIP": 2,
        }

        frame["_rank"] = (
            frame[
                "decision"
            ]
            .map(rank)
            .fillna(9)
        )

        frame = (
            frame.sort_values(
                [
                    "_rank",
                    "conviction",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .drop(
                columns=[
                    "_rank"
                ]
            )
            .reset_index(
                drop=True
            )
        )

    audit = {
        "schema": (
            "portfolio_decision_v2_7"
        ),
        "proposal_count": int(
            len(frame)
        ),
        "buy_new": int(
            (
                frame[
                    "decision"
                ]
                == "BUY_NEW"
            ).sum()
        )
        if not frame.empty
        else 0,
        "observe_existing": int(
            (
                frame[
                    "decision"
                ]
                == (
                    "OBSERVE_EXISTING_"
                    "POSITION_STATE"
                )
            ).sum()
        )
        if not frame.empty
        else 0,
        "shariah_verified": int(
            frame[
                "shariah_verified"
            ].sum()
        )
        if not frame.empty
        else 0,
        "whole_share_canary": True,
        "fractional_shares_allowed": False,
        "fixed_euro_order_cap_enabled": False,
        "broker_submission_enabled": False,
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
