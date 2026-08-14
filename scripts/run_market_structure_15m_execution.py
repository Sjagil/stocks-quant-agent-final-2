#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.market_structure_15m_execution import (
    full_history_eligibility,
    load_symbol_frames,
    resolve_market_structure_symbol,
)
from stocks.research.strategy_factory_1h import (
    period_metrics,
)
from stocks.research.walkforward_splits import (
    rolling_periods,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DEFAULT_SYMBOLS = (
    "AAPL",
    "AMD",
    "MSFT",
    "NVDA",
    "SPY",
    "QQQ",
    "GLD",
    "SLV",
    "CPER",
)


def finite_values(
    values,
):
    result = []

    for value in values:
        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if math.isfinite(
            number
        ):
            result.append(
                number
            )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default=",".join(
            DEFAULT_SYMBOLS
        ),
    )

    parser.add_argument(
        "--folds",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--purge-bars",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--base-cost-bps-per-side",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "--stress-cost-bps-per-side",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--min-test-trades",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    symbols = tuple(
        item.strip().upper()
        for item in (
            args.symbols.split(
                ","
            )
        )
        if item.strip()
    )

    factory_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "strategy_factory_1h"
    )

    survivor_path = (
        factory_root
        / "survivors.csv"
    )

    trade_path = (
        factory_root
        / "survivor_trades.parquet"
    )

    if not survivor_path.is_file():
        raise FileNotFoundError(
            survivor_path
        )

    if not trade_path.is_file():
        raise FileNotFoundError(
            trade_path
        )

    survivors = pd.read_csv(
        survivor_path
    )

    factory_trades = pd.read_parquet(
        trade_path
    )

    market = survivors.loc[
        survivors[
            "strategy"
        ]
        == (
            "market_structure_"
            "atr_pullback"
        )
    ].copy()

    if market.empty:
        raise ValueError(
            "no market-structure "
            "survivors"
        )

    frames = {}
    fifteen_frames = {}
    source_rows = []
    eligibility_rows = []

    for symbol in symbols:
        (
            one_hour,
            fifteen,
            one_source,
            fifteen_source,
        ) = load_symbol_frames(
            ROOT,
            symbol,
        )

        frames[
            symbol
        ] = one_hour

        fifteen_frames[
            symbol
        ] = fifteen

        eligibility = (
            full_history_eligibility(
                one_hour,
                fifteen,
            )
        )

        eligibility_rows.append(
            {
                "symbol": symbol,
                **eligibility,
            }
        )

        source_rows.append(
            {
                "symbol": symbol,
                "one_hour_source": (
                    str(
                        one_source
                    )
                ),
                "fifteen_minute_source": (
                    str(
                        fifteen_source
                    )
                ),
            }
        )

        print()
        print(
            symbol,
        )

        print(
            "FULL_HISTORY_ELIGIBLE",
            eligibility[
                "eligible"
            ],
        )

        print(
            "FIRST_1H",
            eligibility[
                "first_1h"
            ],
        )

        print(
            "FIRST_15M",
            eligibility[
                "first_15m"
            ],
        )

    eligibility_frame = (
        pd.DataFrame(
            eligibility_rows
        )
    )

    eligible_symbols = set(
        eligibility_frame.loc[
            eligibility_frame[
                "eligible"
            ],
            "symbol",
        ]
        .astype(str)
        .tolist()
    )

    if len(
        eligible_symbols
    ) < 7:
        raise ValueError(
            "fewer than seven symbols "
            "have full-history 15m"
        )

    if "SPY" not in frames:
        raise ValueError(
            "SPY required as WFO anchor"
        )

    anchor_index = (
        pd.DatetimeIndex(
            pd.to_datetime(
                frames[
                    "SPY"
                ][
                    "date"
                ],
                utc=True,
            )
        )
        .sort_values()
        .drop_duplicates()
    )

    folds = rolling_periods(
        anchor_index,
        hold_bars=int(
            args.purge_bars
        ),
        requested_folds=int(
            args.folds
        ),
    )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / (
            "market_structure_"
            "15m_execution"
        )
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_resolved = []
    all_audits = []
    fold_rows = []
    summary_rows = []

    for _, survivor in (
        market.iterrows()
    ):
        hypothesis_id = str(
            survivor[
                "hypothesis_id"
            ]
        )

        params = json.loads(
            survivor[
                "params_json"
            ]
        )

        print()
        print(
            "=" * 78
        )

        print(
            hypothesis_id
        )

        resolved_parts = []
        hypothesis_audits = []

        for symbol in symbols:
            eligibility = (
                eligibility_frame.loc[
                    eligibility_frame[
                        "symbol"
                    ]
                    == symbol
                ]
                .iloc[
                    0
                ]
            )

            if not bool(
                eligibility[
                    "eligible"
                ]
            ):
                audit = {
                    "symbol": symbol,
                    "hypothesis_id": (
                        hypothesis_id
                    ),
                    "path_complete": False,
                    "path_failure": (
                        "INCOMPLETE_"
                        "HISTORICAL_15M"
                    ),
                    "resolved_trades": 0,
                    "required_15m_hours": 0,
                    "complete_15m_hours": 0,
                    "threshold_hour_coverage": (
                        math.nan
                    ),
                    "execution_authority": (
                        "NONE"
                    ),
                    "broker_calls": 0,
                }

                hypothesis_audits.append(
                    audit
                )

                all_audits.append(
                    audit
                )

                print(
                    symbol,
                    "EXCLUDED_INCOMPLETE_HISTORY",
                )

                continue

            (
                resolved,
                audit,
            ) = (
                resolve_market_structure_symbol(
                    frames[
                        symbol
                    ],
                    fifteen_frames[
                        symbol
                    ],
                    symbol=symbol,
                    hypothesis_id=(
                        hypothesis_id
                    ),
                    params=params,
                )
            )

            hypothesis_audits.append(
                audit
            )

            all_audits.append(
                audit
            )

            print(
                symbol,
                "PATH_COMPLETE",
                audit[
                    "path_complete"
                ],
                "TRADES",
                audit[
                    "resolved_trades"
                ],
                "THRESHOLD_COVERAGE",
                audit[
                    "threshold_hour_coverage"
                ],
                "FAILURE",
                audit[
                    "path_failure"
                ],
            )

            if (
                audit[
                    "path_complete"
                ]
                and not resolved.empty
            ):
                resolved_parts.append(
                    resolved
                )

        validated_symbols = {
            str(
                audit[
                    "symbol"
                ]
            )
            for audit
            in hypothesis_audits
            if (
                audit[
                    "path_complete"
                ]
                and audit[
                    "symbol"
                ]
                in eligible_symbols
            )
        }

        validated_ratio = (
            len(
                validated_symbols
            )
            / max(
                len(
                    eligible_symbols
                ),
                1,
            )
        )

        if resolved_parts:
            resolved = (
                pd.concat(
                    resolved_parts,
                    ignore_index=True,
                )
                .sort_values(
                    [
                        "entry_time",
                        "symbol",
                    ]
                )
                .reset_index(
                    drop=True
                )
            )
        else:
            resolved = pd.DataFrame()

        if not resolved.empty:
            all_resolved.append(
                resolved
            )

        baseline = factory_trades.loc[
            (
                factory_trades[
                    "hypothesis_id"
                ]
                .astype(str)
                == hypothesis_id
            )
            & (
                factory_trades[
                    "symbol"
                ]
                .astype(str)
                .isin(
                    validated_symbols
                )
            )
        ].copy()

        fold_group = []

        for (
            fold_number,
            periods,
        ) in enumerate(
            folds,
            start=1,
        ):
            baseline_base = (
                period_metrics(
                    baseline,
                    periods[
                        "test"
                    ],
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            resolved_base = (
                period_metrics(
                    resolved,
                    periods[
                        "test"
                    ],
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            resolved_stress = (
                period_metrics(
                    resolved,
                    periods[
                        "test"
                    ],
                    cost_bps_per_side=(
                        args
                        .stress_cost_bps_per_side
                    ),
                )
            )

            row = {
                "hypothesis_id": (
                    hypothesis_id
                ),
                "fold": (
                    fold_number
                ),
                "validated_symbols": (
                    len(
                        validated_symbols
                    )
                ),
                "baseline_trades": (
                    baseline_base[
                        "trades"
                    ]
                ),
                "baseline_expectancy_bps": (
                    baseline_base[
                        "net_expectancy_bps"
                    ]
                ),
                "resolved_trades": (
                    resolved_base[
                        "trades"
                    ]
                ),
                "resolved_expectancy_bps": (
                    resolved_base[
                        "net_expectancy_bps"
                    ]
                ),
                "resolved_profit_factor": (
                    resolved_base[
                        "profit_factor"
                    ]
                ),
                "resolved_stress_expectancy_bps": (
                    resolved_stress[
                        "net_expectancy_bps"
                    ]
                ),
            }

            fold_rows.append(
                row
            )

            fold_group.append(
                row
            )

            print(
                "FOLD",
                fold_number,
                "BASELINE_BPS",
                row[
                    "baseline_expectancy_bps"
                ],
                "RESOLVED_BPS",
                row[
                    "resolved_expectancy_bps"
                ],
                "STRESS_BPS",
                row[
                    "resolved_stress_expectancy_bps"
                ],
                "TRADES",
                row[
                    "resolved_trades"
                ],
            )

        usable = [
            row
            for row
            in fold_group
            if (
                row[
                    "resolved_trades"
                ]
                >= args.min_test_trades
            )
        ]

        base_values = finite_values(
            row[
                "resolved_expectancy_bps"
            ]
            for row
            in usable
        )

        stress_values = finite_values(
            row[
                "resolved_stress_expectancy_bps"
            ]
            for row
            in usable
        )

        pf_values = finite_values(
            row[
                "resolved_profit_factor"
            ]
            for row
            in usable
        )

        usable_folds = len(
            usable
        )

        positive_ratio = (
            float(
                np.mean(
                    np.asarray(
                        base_values
                    )
                    > 0
                )
            )
            if base_values
            else 0.0
        )

        stress_positive_ratio = (
            float(
                np.mean(
                    np.asarray(
                        stress_values
                    )
                    > 0
                )
            )
            if stress_values
            else 0.0
        )

        median_expectancy = (
            float(
                np.median(
                    base_values
                )
            )
            if base_values
            else math.nan
        )

        worst_expectancy = (
            float(
                np.min(
                    base_values
                )
            )
            if base_values
            else math.nan
        )

        median_stress = (
            float(
                np.median(
                    stress_values
                )
            )
            if stress_values
            else math.nan
        )

        median_pf = (
            float(
                np.median(
                    pf_values
                )
            )
            if pf_values
            else math.nan
        )

        data_gate = (
            len(
                validated_symbols
            )
            >= 7
            and validated_ratio
            >= 0.875
        )

        performance_gate = (
            usable_folds
            >= 3
            and positive_ratio
            >= 0.75
            and stress_positive_ratio
            >= 0.75
            and math.isfinite(
                median_expectancy
            )
            and median_expectancy
            > 0
            and math.isfinite(
                worst_expectancy
            )
            and worst_expectancy
            > 0
            and math.isfinite(
                median_stress
            )
            and median_stress
            > 0
            and math.isfinite(
                median_pf
            )
            and median_pf
            > 1.10
        )

        if (
            data_gate
            and performance_gate
        ):
            status = (
                "15M_EXECUTION_VALIDATED"
            )
        elif data_gate:
            status = (
                "15M_EXECUTION_REJECT"
            )
        else:
            status = (
                "15M_EXECUTION_INCOMPLETE"
            )

        summary_rows.append(
            {
                "hypothesis_id": (
                    hypothesis_id
                ),
                "factory_status": (
                    survivor[
                        "status"
                    ]
                ),
                "eligible_symbols": (
                    len(
                        eligible_symbols
                    )
                ),
                "validated_symbols": (
                    len(
                        validated_symbols
                    )
                ),
                "validated_symbol_ratio": (
                    validated_ratio
                ),
                "baseline_trades": int(
                    len(
                        baseline
                    )
                ),
                "resolved_trades": int(
                    len(
                        resolved
                    )
                ),
                "usable_folds": (
                    usable_folds
                ),
                "positive_fold_ratio": (
                    positive_ratio
                ),
                "stress_positive_fold_ratio": (
                    stress_positive_ratio
                ),
                "median_resolved_expectancy_bps": (
                    median_expectancy
                ),
                "worst_resolved_expectancy_bps": (
                    worst_expectancy
                ),
                "median_stress_expectancy_bps": (
                    median_stress
                ),
                "median_resolved_profit_factor": (
                    median_pf
                ),
                "resolved_same_1h_entry_exit": (
                    int(
                        resolved[
                            "same_1h_entry_exit"
                        ].sum()
                    )
                    if not resolved.empty
                    else 0
                ),
                "resolved_same_15m_entry_exit": (
                    int(
                        resolved[
                            "same_15m_entry_exit"
                        ].sum()
                    )
                    if not resolved.empty
                    else 0
                ),
                "status": (
                    status
                ),
            }
        )

    audit_frame = pd.DataFrame(
        all_audits
    )

    fold_frame = pd.DataFrame(
        fold_rows
    )

    summary = pd.DataFrame(
        summary_rows
    )

    eligibility_frame.to_csv(
        output_root
        / "symbol_eligibility.csv",
        index=False,
    )

    pd.DataFrame(
        source_rows
    ).to_csv(
        output_root
        / "sources.csv",
        index=False,
    )

    audit_frame.to_csv(
        output_root
        / "coverage.csv",
        index=False,
    )

    fold_frame.to_csv(
        output_root
        / "folds.csv",
        index=False,
    )

    summary.to_csv(
        output_root
        / "summary.csv",
        index=False,
    )

    if all_resolved:
        pd.concat(
            all_resolved,
            ignore_index=True,
        ).to_parquet(
            output_root
            / "resolved_trades.parquet",
            index=False,
        )

    audit = {
        "schema": (
            "market_structure_"
            "15m_execution_v1"
        ),
        "primary_timeframe": (
            "1h"
        ),
        "execution_timeframe": (
            "15m"
        ),
        "strategy": (
            "market_structure_"
            "atr_pullback"
        ),
        "factory_survivors": int(
            len(
                market
            )
        ),
        "eligible_symbols": sorted(
            eligible_symbols
        ),
        "excluded_symbols": sorted(
            set(
                symbols
            )
            - eligible_symbols
        ),
        "fold_count": int(
            len(
                folds
            )
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "automatic_orders": 0,
        "rule": (
            "15m resolves execution "
            "chronology only; it cannot "
            "create the 1h swing thesis"
        ),
    }

    (
        output_root
        / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "=" * 78
    )

    print(
        "MARKET STRUCTURE "
        "15M EXECUTION"
    )

    print(
        "=" * 78
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "ARTIFACT_ROOT",
        output_root,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
