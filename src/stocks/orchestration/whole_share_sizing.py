from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
)
from stocks.research.dynamic_universe_generalization import (
    discover_interval_sources,
)
from stocks.research.strategy_factory_1h import (
    prepare_one_hour_frame,
)


ACTIVE_ORDER_STATUSES = {
    "PENDINGSUBMIT",
    "APIPENDING",
    "PRESUBMITTED",
    "SUBMITTED",
    "PENDINGCANCEL",
}


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return (
        number
        if math.isfinite(number)
        else None
    )


def _integer_floor(value: float) -> int:
    if not math.isfinite(value):
        return 0
    return max(0, int(math.floor(value)))


def select_risk_fraction(
    conviction: float,
    *,
    base: float,
    strong: float,
    threshold: float,
    hard_max: float,
) -> float:
    chosen = (
        strong
        if conviction >= threshold
        else base
    )
    return min(
        float(chosen),
        float(hard_max),
    )


def stop_distance_from_atr(
    *,
    price: float,
    atr: float,
    atr_multiple: float,
    minimum_stop_fraction: float,
) -> float:
    if price <= 0:
        raise ValueError(
            "price must be positive"
        )
    if atr < 0:
        raise ValueError(
            "atr must be non-negative"
        )

    return max(
        float(atr) * float(atr_multiple),
        float(price)
        * float(minimum_stop_fraction),
    )


def compute_whole_share_quantity(
    *,
    net_liquidation_eur: float,
    execution_capacity_eur: float,
    price_eur: float,
    stop_distance_eur: float,
    risk_fraction: float,
    cash_floor_fraction: float,
    maximum_single_weight: float,
    existing_symbol_notional_eur: float = 0.0,
) -> dict[str, Any]:
    if (
        net_liquidation_eur <= 0
        or execution_capacity_eur < 0
        or price_eur <= 0
        or stop_distance_eur <= 0
    ):
        return {
            "quantity": 0,
            "reason": "INVALID_SIZING_INPUT",
        }

    risk_budget = (
        net_liquidation_eur
        * risk_fraction
    )
    cash_reserve = (
        net_liquidation_eur
        * cash_floor_fraction
    )
    deployable_cash = max(
        0.0,
        execution_capacity_eur
        - cash_reserve,
    )
    single_name_capacity = max(
        0.0,
        net_liquidation_eur
        * maximum_single_weight
        - existing_symbol_notional_eur,
    )

    qty_risk = _integer_floor(
        risk_budget
        / stop_distance_eur
    )
    qty_cash = _integer_floor(
        deployable_cash
        / price_eur
    )
    qty_weight = _integer_floor(
        single_name_capacity
        / price_eur
    )

    quantity = min(
        qty_risk,
        qty_cash,
        qty_weight,
    )

    return {
        "quantity": int(quantity),
        "qty_risk": qty_risk,
        "qty_cash": qty_cash,
        "qty_weight": qty_weight,
        "risk_budget_eur": risk_budget,
        "cash_reserve_eur": cash_reserve,
        "deployable_cash_eur": deployable_cash,
        "single_name_capacity_eur": (
            single_name_capacity
        ),
        "estimated_position_notional_eur": (
            quantity * price_eur
        ),
        "estimated_stop_risk_eur": (
            quantity * stop_distance_eur
        ),
        "reason": (
            "WHOLE_SHARE_SIZE_AVAILABLE"
            if quantity >= 1
            else (
                "WHOLE_SHARE_MINIMUM_NOT_"
                "AFFORDABLE_OR_RISK_TOO_SMALL"
            )
        ),
    }


def _position_map(
    snapshot: dict[str, Any],
) -> dict[str, dict[str, float]]:
    positions = (
        (
            snapshot.get("positions")
            or {}
        ).get("positions")
        or []
    )

    output: dict[
        str,
        dict[str, float],
    ] = {}

    for row in positions:
        symbol = str(
            row.get("symbol")
            or ""
        ).upper()
        quantity = _number(
            row.get("position_quantity")
        )
        average_cost = _number(
            row.get("average_cost")
        )

        if (
            not symbol
            or quantity is None
            or average_cost is None
        ):
            continue

        output[symbol] = {
            "quantity": quantity,
            "average_cost": average_cost,
            "approx_notional_eur": abs(
                quantity * average_cost
            ),
        }

    return output


def build_whole_share_sizing(
    project_root: str | Path,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    root = Path(
        project_root
    ).resolve()

    proposals_path = (
        root
        / "artifacts/research_runtime/"
        "portfolio_decision_v2_7/"
        "proposals.csv"
    )
    broker_path = (
        root
        / "artifacts/research_runtime/"
        "ibkr_readonly_v2_9/"
        "snapshot.json"
    )

    if not proposals_path.is_file():
        return pd.DataFrame(), {
            "schema": "whole_share_sizing_v2_9",
            "rows": 0,
            "reason": "PORTFOLIO_PROPOSALS_MISSING",
            "execution_authority": "NONE",
        }

    if not broker_path.is_file():
        return pd.DataFrame(), {
            "schema": "whole_share_sizing_v2_9",
            "rows": 0,
            "reason": "IBKR_READONLY_SNAPSHOT_MISSING",
            "execution_authority": "NONE",
        }

    proposals = pd.read_csv(
        proposals_path
    )
    broker = json.loads(
        broker_path.read_text(
            encoding="utf-8"
        )
    )
    economic = (
        broker.get(
            "economic_account_state"
        )
        or {}
    )
    snapshot = (
        broker.get("snapshot")
        or {}
    )

    policy = json.loads(
        (
            root
            / "config/"
            "final_decision_fabric_v2_9.json"
        ).read_text(
            encoding="utf-8"
        )
    )["whole_share_sizing"]

    net_liq = _number(
        economic.get(
            "reporting_value_eur"
        )
    )
    capacity = _number(
        economic.get(
            "execution_sizing_capacity_eur"
        )
    )

    account_ready = (
        economic.get("execution_status")
        == "EXECUTION_ACCOUNT_READY"
        and bool(
            broker.get(
                "double_snapshot_stable"
            )
        )
        and int(
            broker.get(
                "broker_write_calls",
                0,
            )
        )
        == 0
    )

    if (
        net_liq is None
        or capacity is None
    ):
        account_ready = False

    positions = _position_map(
        snapshot
    )
    position_count = sum(
        1
        for row in positions.values()
        if abs(row["quantity"]) > 0
    )

    sources = discover_interval_sources(
        root,
        "1h",
    )

    rows: list[
        dict[str, Any]
    ] = []

    for proposal in proposals.to_dict(
        orient="records"
    ):
        if str(
            proposal.get("decision")
        ) != "BUY_NEW":
            continue

        symbol = str(
            proposal["symbol"]
        ).upper()

        blockers: list[str] = []

        if not account_ready:
            blockers.append(
                "IBKR_EXECUTION_ACCOUNT_NOT_READY"
            )

        if position_count >= int(
            policy["maximum_positions"]
        ):
            blockers.append(
                "MAXIMUM_POSITION_COUNT_REACHED"
            )

        existing = positions.get(
            symbol,
            {
                "quantity": 0.0,
                "approx_notional_eur": 0.0,
            },
        )

        if abs(
            float(
                existing.get(
                    "quantity",
                    0.0,
                )
            )
        ) > 0:
            blockers.append(
                "SYMBOL_ALREADY_HELD"
            )

        path = sources.get(
            symbol
        )

        if path is None:
            blockers.append(
                "CANONICAL_1H_SOURCE_MISSING"
            )
            frame = None
        else:
            try:
                frame = (
                    prepare_one_hour_frame(
                        pd.read_parquet(path),
                        symbol,
                    )
                )
            except Exception:
                frame = None
                blockers.append(
                    "CANONICAL_1H_SOURCE_INVALID"
                )

        price = None
        atr = None
        stop = None
        quantity_data = {
            "quantity": 0,
            "reason": (
                "SIZING_NOT_EVALUABLE"
            ),
        }

        if (
            frame is not None
            and not frame.empty
        ):
            cache = FeatureCache(
                frame
            )
            price = _number(
                frame["close"].iloc[-1]
            )
            atr_values = cache.atr(
                int(
                    policy["atr_period"]
                )
            )
            atr = (
                _number(atr_values[-1])
                if len(atr_values)
                else None
            )

        if (
            price is None
            or atr is None
            or price <= 0
            or atr < 0
        ):
            blockers.append(
                "PRICE_OR_ATR_NOT_AVAILABLE"
            )
        elif (
            net_liq is not None
            and capacity is not None
        ):
            stop = stop_distance_from_atr(
                price=price,
                atr=atr,
                atr_multiple=float(
                    policy[
                        "stop_atr_multiple"
                    ]
                ),
                minimum_stop_fraction=float(
                    policy[
                        "minimum_stop_fraction"
                    ]
                ),
            )

            conviction = float(
                proposal.get(
                    "conviction",
                    0.0,
                )
                or 0.0
            )
            risk_fraction = (
                select_risk_fraction(
                    conviction,
                    base=float(
                        policy[
                            "base_risk_fraction"
                        ]
                    ),
                    strong=float(
                        policy[
                            "strong_risk_fraction"
                        ]
                    ),
                    threshold=float(
                        policy[
                            "strong_conviction_threshold"
                        ]
                    ),
                    hard_max=float(
                        policy[
                            "hard_max_risk_fraction"
                        ]
                    ),
                )
            )

            quantity_data = (
                compute_whole_share_quantity(
                    net_liquidation_eur=net_liq,
                    execution_capacity_eur=capacity,
                    price_eur=price,
                    stop_distance_eur=stop,
                    risk_fraction=risk_fraction,
                    cash_floor_fraction=float(
                        policy[
                            "cash_floor"
                        ]
                    ),
                    maximum_single_weight=float(
                        policy[
                            "maximum_single_weight"
                        ]
                    ),
                    existing_symbol_notional_eur=float(
                        existing.get(
                            "approx_notional_eur",
                            0.0,
                        )
                    ),
                )
            )

            if int(
                quantity_data[
                    "quantity"
                ]
            ) < int(
                policy[
                    "minimum_quantity"
                ]
            ):
                blockers.append(
                    str(
                        quantity_data[
                            "reason"
                        ]
                    )
                )

        quantity = int(
            quantity_data.get(
                "quantity",
                0,
            )
        )

        rows.append(
            {
                "symbol": symbol,
                "source_decision": "BUY_NEW",
                "conviction": proposal.get(
                    "conviction"
                ),
                "reference_price_eur": price,
                "atr_eur": atr,
                "stop_distance_eur": stop,
                "net_liquidation_eur": net_liq,
                "execution_capacity_eur": capacity,
                "existing_quantity": existing.get(
                    "quantity",
                    0.0,
                ),
                "whole_share_quantity": (
                    quantity
                ),
                "estimated_position_notional_eur": (
                    quantity_data.get(
                        "estimated_position_notional_eur"
                    )
                ),
                "estimated_stop_risk_eur": (
                    quantity_data.get(
                        "estimated_stop_risk_eur"
                    )
                ),
                "risk_budget_eur": quantity_data.get(
                    "risk_budget_eur"
                ),
                "cash_reserve_eur": quantity_data.get(
                    "cash_reserve_eur"
                ),
                "quantity_mode": "WHOLE_SHARES",
                "fractional_shares_allowed": False,
                "fixed_euro_order_cap_enabled": False,
                "sizing_ready": (
                    quantity >= 1
                    and not blockers
                ),
                "blockers": "|".join(
                    sorted(
                        set(blockers)
                    )
                ),
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            }
        )

    frame = pd.DataFrame(
        rows
    )

    audit = {
        "schema": "whole_share_sizing_v2_9",
        "buy_new_inputs": int(
            (
                proposals.get(
                    "decision",
                    pd.Series(dtype=str),
                )
                == "BUY_NEW"
            ).sum()
        )
        if not proposals.empty
        else 0,
        "rows": int(
            len(frame)
        ),
        "sizing_ready": int(
            frame.get(
                "sizing_ready",
                pd.Series(dtype=bool),
            )
            .fillna(False)
            .astype(bool)
            .sum()
        )
        if not frame.empty
        else 0,
        "account_ready": bool(
            account_ready
        ),
        "whole_shares_only": True,
        "fixed_euro_order_cap_enabled": False,
        "portfolio_heat_authority": (
            "NOT_GRANTED_V2_9"
        ),
        "broker_submission_enabled": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }

    return frame, audit
