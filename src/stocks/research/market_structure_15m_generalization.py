
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stocks.research.market_structure_15m_execution import (
    full_history_eligibility,
    load_symbol_frames,
    resolve_market_structure_symbol,
)
from stocks.research.strategy_factory_1h import (
    period_metrics,
    trade_metrics,
)
from stocks.research.walkforward_splits import (
    rolling_periods,
)


def _read_csv(path: Path) -> pd.DataFrame:
    return (
        pd.read_csv(path)
        if path.is_file()
        else pd.DataFrame()
    )


def _finite(values) -> list[float]:
    output: list[float] = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            output.append(number)
    return output


def _champion(root: Path) -> dict[str, Any]:
    roster = _read_csv(
        root
        / "artifacts/research_runtime/"
        "final_strategy_roster/roster.csv"
    )

    if roster.empty:
        raise FileNotFoundError(
            "final strategy roster missing"
        )

    rows = roster.loc[
        (
            roster["strategy"]
            == "market_structure_atr_pullback"
        )
        & roster["cluster_champion"]
        .fillna(False)
        .astype(bool)
    ]

    if rows.empty:
        raise ValueError(
            "market-structure cluster champion missing"
        )

    return rows.iloc[0].to_dict()


def build_market_structure_15m_generalization(
    project_root: str | Path,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    root = Path(project_root).resolve()
    champion = _champion(root)

    holdout = json.loads(
        (
            root
            / "config/generalization_holdout_v1.json"
        ).read_text(encoding="utf-8")
    )

    policy = json.loads(
        (
            root
            / "config/final_decision_fabric_v2_7.json"
        ).read_text(encoding="utf-8")
    )[
        "market_structure_15m_generalization"
    ]

    params = json.loads(
        str(champion["params_json"])
    )
    hypothesis_id = str(
        champion["hypothesis_id"]
    )

    source_rows: list[dict[str, Any]] = []
    trade_parts: list[pd.DataFrame] = []
    anchor_index: pd.DatetimeIndex | None = None

    for symbol_raw in holdout["symbols"]:
        symbol = str(symbol_raw).upper()

        try:
            (
                one_hour,
                fifteen,
                one_path,
                fifteen_path,
            ) = load_symbol_frames(
                root,
                symbol,
            )

            eligibility = (
                full_history_eligibility(
                    one_hour,
                    fifteen,
                )
            )

        except Exception as exc:
            source_rows.append(
                {
                    "symbol": symbol,
                    "eligible": False,
                    "reason": (
                        f"{type(exc).__name__}:{exc}"
                    ),
                    "one_hour_source": None,
                    "fifteen_minute_source": None,
                }
            )
            continue

        source_rows.append(
            {
                "symbol": symbol,
                **eligibility,
                "reason": (
                    None
                    if eligibility["eligible"]
                    else "INCOMPLETE_15M_HISTORY"
                ),
                "one_hour_source": str(one_path),
                "fifteen_minute_source": str(
                    fifteen_path
                ),
            }
        )

        if not eligibility["eligible"]:
            continue

        if anchor_index is None:
            anchor_index = (
                pd.DatetimeIndex(
                    pd.to_datetime(
                        one_hour["date"],
                        utc=True,
                    )
                )
                .sort_values()
                .drop_duplicates()
            )

        trades, path_audit = (
            resolve_market_structure_symbol(
                one_hour,
                fifteen,
                symbol=symbol,
                hypothesis_id=hypothesis_id,
                params=params,
            )
        )

        if not path_audit["path_complete"]:
            source_rows[-1]["eligible"] = False
            source_rows[-1]["reason"] = (
                "15M_PATH_INCOMPLETE:"
                + str(
                    path_audit["path_failure"]
                )
            )
            continue

        if not trades.empty:
            trade_parts.append(trades)

    sources = pd.DataFrame(source_rows)

    trades = (
        pd.concat(
            trade_parts,
            ignore_index=True,
        )
        .sort_values(
            [
                "entry_time",
                "symbol",
            ]
        )
        .reset_index(drop=True)
        if trade_parts
        else pd.DataFrame()
    )

    eligible_mask = (
        sources.get(
            "eligible",
            pd.Series(
                False,
                index=sources.index,
            ),
        )
        .fillna(False)
        .astype(bool)
    )

    eligible_count = int(
        eligible_mask.sum()
    )

    missing = (
        sources.loc[
            ~eligible_mask,
            [
                "symbol",
                "reason",
            ],
        ].copy()
        if not sources.empty
        else pd.DataFrame(
            columns=[
                "symbol",
                "reason",
            ]
        )
    )

    minimum_available = int(
        policy["minimum_symbols_available"]
    )

    if (
        eligible_count < minimum_available
        or anchor_index is None
        or len(anchor_index) < 4000
    ):
        audit = {
            "schema": (
                "market_structure_"
                "15m_generalization_v2_7"
            ),
            "hypothesis_id": hypothesis_id,
            "status": (
                "NOT_EVALUABLE_15M_DATA_MISSING"
            ),
            "eligible_symbols": eligible_count,
            "required_symbols": minimum_available,
            "traded_symbols": (
                int(
                    trades["symbol"].nunique()
                )
                if not trades.empty
                else 0
            ),
            "oos_trades": 0,
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
        }

        return (
            pd.DataFrame(),
            missing,
            trades,
            audit,
        )

    folds = rolling_periods(
        anchor_index,
        hold_bars=int(
            policy["purge_bars"]
        ),
        requested_folds=int(
            policy["folds"]
        ),
    )

    fold_rows: list[dict[str, Any]] = []

    for number, periods in enumerate(
        folds,
        start=1,
    ):
        base = period_metrics(
            trades,
            periods["test"],
            cost_bps_per_side=float(
                policy[
                    "base_cost_bps_per_side"
                ]
            ),
        )
        stress = period_metrics(
            trades,
            periods["test"],
            cost_bps_per_side=float(
                policy[
                    "stress_cost_bps_per_side"
                ]
            ),
        )

        fold_rows.append(
            {
                "fold": number,
                "trades": int(
                    base["trades"]
                ),
                "expectancy_bps": (
                    base[
                        "net_expectancy_bps"
                    ]
                ),
                "stress_expectancy_bps": (
                    stress[
                        "net_expectancy_bps"
                    ]
                ),
                "profit_factor": (
                    base["profit_factor"]
                ),
            }
        )

    symbol_rows: list[
        dict[str, Any]
    ] = []

    for symbol, part in (
        trades.groupby("symbol")
    ):
        base = trade_metrics(
            part,
            cost_bps_per_side=float(
                policy[
                    "base_cost_bps_per_side"
                ]
            ),
        )
        stress = trade_metrics(
            part,
            cost_bps_per_side=float(
                policy[
                    "stress_cost_bps_per_side"
                ]
            ),
        )

        symbol_rows.append(
            {
                "symbol": symbol,
                "trades": int(
                    base["trades"]
                ),
                "expectancy_bps": (
                    base[
                        "net_expectancy_bps"
                    ]
                ),
                "stress_expectancy_bps": (
                    stress[
                        "net_expectancy_bps"
                    ]
                ),
                "profit_factor": (
                    base["profit_factor"]
                ),
            }
        )

    folds_frame = pd.DataFrame(
        fold_rows
    )
    symbols_frame = pd.DataFrame(
        symbol_rows
    )

    fold_ok = (
        folds_frame["trades"]
        >= int(
            policy[
                "minimum_fold_trades"
            ]
        )
    )

    symbol_ok = (
        symbols_frame["trades"]
        >= int(
            policy[
                "minimum_symbol_trades"
            ]
        )
    )

    positive_fold_ratio = (
        float(
            (
                folds_frame.loc[
                    fold_ok,
                    "expectancy_bps",
                ]
                > 0
            ).mean()
        )
        if bool(fold_ok.any())
        else 0.0
    )

    stress_positive_fold_ratio = (
        float(
            (
                folds_frame.loc[
                    fold_ok,
                    "stress_expectancy_bps",
                ]
                > 0
            ).mean()
        )
        if bool(fold_ok.any())
        else 0.0
    )

    positive_symbol_ratio = (
        float(
            (
                symbols_frame.loc[
                    symbol_ok,
                    "expectancy_bps",
                ]
                > 0
            ).mean()
        )
        if bool(symbol_ok.any())
        else 0.0
    )

    stress_positive_symbol_ratio = (
        float(
            (
                symbols_frame.loc[
                    symbol_ok,
                    "stress_expectancy_bps",
                ]
                > 0
            ).mean()
        )
        if bool(symbol_ok.any())
        else 0.0
    )

    expectations = _finite(
        symbols_frame.loc[
            symbol_ok,
            "expectancy_bps",
        ]
    )

    stress_expectations = _finite(
        symbols_frame.loc[
            symbol_ok,
            "stress_expectancy_bps",
        ]
    )

    total_trades = int(
        len(trades)
    )

    traded_symbols = int(
        trades["symbol"].nunique()
    )

    max_symbol_share = (
        float(
            trades[
                "symbol"
            ]
            .value_counts()
            .max()
            / total_trades
        )
        if total_trades
        else 1.0
    )

    passed = (
        traded_symbols
        >= int(
            policy[
                "minimum_symbols_traded"
            ]
        )
        and total_trades
        >= int(
            policy[
                "minimum_oos_trades"
            ]
        )
        and positive_symbol_ratio
        >= float(
            policy[
                "minimum_positive_symbol_ratio"
            ]
        )
        and positive_fold_ratio
        >= float(
            policy[
                "minimum_positive_fold_ratio"
            ]
        )
        and stress_positive_fold_ratio
        >= float(
            policy[
                "minimum_stress_positive_fold_ratio"
            ]
        )
        and stress_positive_symbol_ratio
        >= float(
            policy[
                "minimum_stress_positive_symbol_ratio"
            ]
        )
        and max_symbol_share
        <= float(
            policy[
                "maximum_symbol_trade_share"
            ]
        )
        and bool(expectations)
        and bool(
            stress_expectations
        )
        and float(
            np.median(
                expectations
            )
        )
        > 0
        and float(
            np.median(
                stress_expectations
            )
        )
        > 0
    )

    audit = {
        "schema": (
            "market_structure_"
            "15m_generalization_v2_7"
        ),
        "hypothesis_id": (
            hypothesis_id
        ),
        "status": (
            "15M_DYNAMIC_UNIVERSE_VALIDATED"
            if passed
            else (
                "15M_DYNAMIC_UNIVERSE_REJECT"
            )
        ),
        "eligible_symbols": (
            eligible_count
        ),
        "traded_symbols": (
            traded_symbols
        ),
        "oos_trades": total_trades,
        "usable_folds": int(
            fold_ok.sum()
        ),
        "positive_fold_ratio": (
            positive_fold_ratio
        ),
        "stress_positive_fold_ratio": (
            stress_positive_fold_ratio
        ),
        "positive_symbol_ratio": (
            positive_symbol_ratio
        ),
        "stress_positive_symbol_ratio": (
            stress_positive_symbol_ratio
        ),
        "median_expectancy_bps": (
            float(
                np.median(
                    expectations
                )
            )
            if expectations
            else None
        ),
        "median_stress_expectancy_bps": (
            float(
                np.median(
                    stress_expectations
                )
            )
            if stress_expectations
            else None
        ),
        "max_symbol_trade_share": (
            max_symbol_share
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "order_calls": 0,
    }

    return (
        symbols_frame,
        missing,
        trades,
        audit,
    )
