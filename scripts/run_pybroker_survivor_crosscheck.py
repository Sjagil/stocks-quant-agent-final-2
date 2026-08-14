#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.pybroker_crosscheck import (
    classify_crosscheck,
    evaluate_symbol_breadth,
    replay_contract_audit,
    run_pybroker_replay,
)
from stocks.research.strategy_factory_1h import (
    contained_trades,
    prepare_one_hour_frame,
    trade_metrics,
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


def one_hour_source(
    symbol: str,
) -> Path:
    candidates = (
        ROOT
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_1h.parquet",
        ROOT
        / "data"
        / "adjusted"
        / f"{symbol}_1h.parquet",
        ROOT
        / "data"
        / "derived"
        / f"{symbol}_1h.parquet",
        ROOT
        / "data"
        / "processed"
        / f"{symbol}_1h.parquet",
    )

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        f"{symbol}: missing 1h data"
    )


def load_frames(
    symbols,
):
    output = {}

    for symbol in symbols:
        raw = pd.read_parquet(
            one_hour_source(
                symbol
            )
        )

        output[
            symbol
        ] = (
            prepare_one_hour_frame(
                raw,
                symbol,
            )
        )

    return output


def finite(
    values,
):
    return [
        float(
            value
        )
        for value in values
        if (
            value is not None
            and math.isfinite(
                float(
                    value
                )
            )
        )
    ]


def main() -> int:
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--factory-root",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "research_runtime"
            / "strategy_factory_1h"
        ),
    )

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
        "--min-test-trades",
        type=int,
        default=8,
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

    args = (
        parser.parse_args()
    )

    symbols = tuple(
        item.strip().upper()
        for item
        in args.symbols.split(
            ","
        )
        if item.strip()
    )

    survivor_path = (
        args.factory_root
        / "survivors.csv"
    )

    trade_path = (
        args.factory_root
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

    trades = pd.read_parquet(
        trade_path
    )

    if survivors.empty:
        raise ValueError(
            "factory has zero survivors"
        )

    frames = load_frames(
        symbols
    )

    anchor = (
        frames[
            "SPY"
        ]
        if "SPY" in frames
        else next(
            iter(
                frames.values()
            )
        )
    )

    index = (
        pd.DatetimeIndex(
            pd.to_datetime(
                anchor[
                    "date"
                ],
                utc=True,
            )
        )
        .sort_values()
        .drop_duplicates()
    )

    folds = rolling_periods(
        index,
        hold_bars=(
            args.purge_bars
        ),
        requested_folds=(
            args.folds
        ),
    )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "pybroker_crosscheck"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    fold_rows = []
    summaries = []

    for survivor in (
        survivors.itertuples(
            index=False
        )
    ):
        hypothesis_id = str(
            survivor.hypothesis_id
        )

        strategy_name = str(
            survivor.strategy
        )

        hypothesis_trades = (
            trades.loc[
                trades[
                    "hypothesis_id"
                ]
                .astype(str)
                == hypothesis_id
            ]
            .copy()
        )

        print()
        print(
            "=" * 78
        )

        print(
            hypothesis_id,
            strategy_name,
        )

        contract = (
            replay_contract_audit(
                hypothesis_trades,
                strategy=(
                    strategy_name
                ),
            )
        )

        if not contract[
            "compatible"
        ]:
            print(
                "EXECUTION_CONTRACT",
                contract[
                    "execution_contract"
                ],
            )

            print(
                "ROUTE",
                contract[
                    "route"
                ],
            )

            print(
                "REASONS",
                ",".join(
                    contract[
                        "reasons"
                    ]
                ),
            )

            print(
                "SAME_BAR_TRADES",
                contract[
                    "same_bar_trades"
                ],
            )

            summaries.append(
                {
                    "hypothesis_id": (
                        hypothesis_id
                    ),
                    "strategy": (
                        strategy_name
                    ),
                    "factory_status": str(
                        survivor.status
                    ),
                    "usable_folds": 0,
                    "positive_fold_ratio": (
                        math.nan
                    ),
                    "stress_positive_fold_ratio": (
                        math.nan
                    ),
                    "median_base_expectancy_bps": (
                        math.nan
                    ),
                    "worst_base_expectancy_bps": (
                        math.nan
                    ),
                    "median_stress_expectancy_bps": (
                        math.nan
                    ),
                    "minimum_pybroker_"
                    "schedule_match_ratio": (
                        math.nan
                    ),
                    "symbol_count": int(
                        hypothesis_trades[
                            "symbol"
                        ]
                        .nunique()
                    ),
                    "positive_symbol_ratio": (
                        math.nan
                    ),
                    "max_symbol_trade_share": (
                        math.nan
                    ),
                    "execution_contract": (
                        contract[
                            "execution_contract"
                        ]
                    ),
                    "execution_route": (
                        contract[
                            "route"
                        ]
                    ),
                    "same_bar_trades": (
                        contract[
                            "same_bar_trades"
                        ]
                    ),
                    "contract_reasons": (
                        "|".join(
                            contract[
                                "reasons"
                            ]
                        )
                    ),
                    "crosscheck_status": (
                        "ROUTE_TO_15M_"
                        "EXECUTION_VALIDATION"
                    ),
                }
            )

            continue

        usable_rows = []

        crosscheck_trades = []

        for (
            fold_number,
            periods,
        ) in enumerate(
            folds,
            start=1,
        ):
            test_trades = (
                contained_trades(
                    hypothesis_trades,
                    periods[
                        "test"
                    ],
                )
            )

            canonical_base = (
                trade_metrics(
                    test_trades,
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            canonical_stress = (
                trade_metrics(
                    test_trades,
                    cost_bps_per_side=(
                        args
                        .stress_cost_bps_per_side
                    ),
                )
            )

            usable = (
                len(
                    test_trades
                )
                >= args.min_test_trades
            )

            row = {
                "hypothesis_id": (
                    hypothesis_id
                ),
                "strategy": (
                    strategy_name
                ),
                "factory_status": str(
                    survivor.status
                ),
                "fold": (
                    fold_number
                ),
                "test_start": (
                    periods[
                        "test"
                    ][0]
                ),
                "test_end": (
                    periods[
                        "test"
                    ][1]
                ),
                "usable": (
                    bool(
                        usable
                    )
                ),
                "canonical_trades": int(
                    len(
                        test_trades
                    )
                ),
                "canonical_base_expectancy_bps": (
                    canonical_base[
                        "net_expectancy_bps"
                    ]
                ),
                "canonical_base_profit_factor": (
                    canonical_base[
                        "profit_factor"
                    ]
                ),
                "canonical_stress_expectancy_bps": (
                    canonical_stress[
                        "net_expectancy_bps"
                    ]
                ),
                "canonical_stress_profit_factor": (
                    canonical_stress[
                        "profit_factor"
                    ]
                ),
            }

            if (
                not test_trades.empty
            ):
                base_replay = (
                    run_pybroker_replay(
                        frames,
                        test_trades,
                        cost_bps_per_side=(
                            args
                            .base_cost_bps_per_side
                        ),
                    )
                )

                stress_replay = (
                    run_pybroker_replay(
                        frames,
                        test_trades,
                        cost_bps_per_side=(
                            args
                            .stress_cost_bps_per_side
                        ),
                    )
                )

                for (
                    key,
                    value,
                ) in (
                    base_replay.items()
                ):
                    row[
                        f"pybroker_base_{key}"
                    ] = value

                for (
                    key,
                    value,
                ) in (
                    stress_replay.items()
                ):
                    row[
                        f"pybroker_stress_{key}"
                    ] = value

                crosscheck_trades.append(
                    test_trades
                )

            fold_rows.append(
                row
            )

            if usable:
                usable_rows.append(
                    row
                )

            print(
                "FOLD",
                fold_number,
                "TRADES",
                len(
                    test_trades
                ),
                "BASE_BPS",
                canonical_base[
                    "net_expectancy_bps"
                ],
                "STRESS_BPS",
                canonical_stress[
                    "net_expectancy_bps"
                ],
                "MATCH",
                row.get(
                    "pybroker_base_"
                    "schedule_match_ratio"
                ),
            )

        if usable_rows:
            base_expectancy = finite(
                [
                    row[
                        "canonical_base_"
                        "expectancy_bps"
                    ]
                    for row
                    in usable_rows
                ]
            )

            stress_expectancy = finite(
                [
                    row[
                        "canonical_stress_"
                        "expectancy_bps"
                    ]
                    for row
                    in usable_rows
                ]
            )

            positive_ratio = float(
                np.mean(
                    [
                        value > 0
                        for value
                        in base_expectancy
                    ]
                )
            )

            stress_positive_ratio = (
                float(
                    np.mean(
                        [
                            value > 0
                            for value
                            in stress_expectancy
                        ]
                    )
                )
            )

            median_base = float(
                np.median(
                    base_expectancy
                )
            )

            worst_base = float(
                min(
                    base_expectancy
                )
            )

            median_stress = float(
                np.median(
                    stress_expectancy
                )
            )

            match_values = finite(
                [
                    row.get(
                        "pybroker_base_"
                        "schedule_match_ratio"
                    )
                    for row
                    in usable_rows
                ]
            )

            min_match = (
                float(
                    min(
                        match_values
                    )
                )
                if match_values
                else 0.0
            )
        else:
            positive_ratio = 0.0
            stress_positive_ratio = 0.0
            median_base = math.nan
            worst_base = math.nan
            median_stress = math.nan
            min_match = 0.0

        if crosscheck_trades:
            breadth_trades = (
                pd.concat(
                    crosscheck_trades,
                    ignore_index=True,
                )
            )
        else:
            breadth_trades = (
                hypothesis_trades.iloc[
                    0:0
                ]
            )

        breadth = (
            evaluate_symbol_breadth(
                breadth_trades,
                cost_bps_per_side=(
                    args
                    .stress_cost_bps_per_side
                ),
            )
        )

        crosscheck_status = (
            classify_crosscheck(
                usable_folds=(
                    len(
                        usable_rows
                    )
                ),
                positive_fold_ratio=(
                    positive_ratio
                ),
                stress_positive_fold_ratio=(
                    stress_positive_ratio
                ),
                worst_expectancy_bps=(
                    worst_base
                ),
                median_stress_expectancy_bps=(
                    median_stress
                ),
                min_schedule_match_ratio=(
                    min_match
                ),
                positive_symbol_ratio=(
                    breadth[
                        "positive_symbol_ratio"
                    ]
                ),
                max_symbol_trade_share=(
                    breadth[
                        "max_symbol_trade_share"
                    ]
                ),
            )
        )

        if (
            str(
                survivor.status
            )
            == "PROVISIONAL_SURVIVOR"
            and crosscheck_status
            == "CROSS_ENGINE_VALIDATED"
        ):
            crosscheck_status = (
                "CROSS_ENGINE_PROVISIONAL"
            )

        summary = {
            "hypothesis_id": (
                hypothesis_id
            ),
            "strategy": (
                strategy_name
            ),
            "factory_status": str(
                survivor.status
            ),
            "usable_folds": int(
                len(
                    usable_rows
                )
            ),
            "positive_fold_ratio": (
                positive_ratio
            ),
            "stress_positive_fold_ratio": (
                stress_positive_ratio
            ),
            "median_base_expectancy_bps": (
                median_base
            ),
            "worst_base_expectancy_bps": (
                worst_base
            ),
            "median_stress_expectancy_bps": (
                median_stress
            ),
            "minimum_pybroker_"
            "schedule_match_ratio": (
                min_match
            ),
            "symbol_count": (
                breadth[
                    "symbol_count"
                ]
            ),
            "positive_symbol_ratio": (
                breadth[
                    "positive_symbol_ratio"
                ]
            ),
            "max_symbol_trade_share": (
                breadth[
                    "max_symbol_trade_share"
                ]
            ),
            "execution_contract": (
                contract[
                    "execution_contract"
                ]
            ),
            "execution_route": (
                contract[
                    "route"
                ]
            ),
            "same_bar_trades": (
                contract[
                    "same_bar_trades"
                ]
            ),
            "contract_reasons": (
                "|".join(
                    contract[
                        "reasons"
                    ]
                )
            ),
            "crosscheck_status": (
                crosscheck_status
            ),
        }

        summaries.append(
            summary
        )

        symbol_path = (
            output_root
            / (
                f"{hypothesis_id}_"
                "symbol_breadth.json"
            )
        )

        symbol_path.write_text(
            json.dumps(
                breadth[
                    "symbol_metrics"
                ],
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

    folds_frame = (
        pd.DataFrame(
            fold_rows
        )
    )

    summary_frame = (
        pd.DataFrame(
            summaries
        )
        .sort_values(
            [
                "crosscheck_status",
                "median_stress_expectancy_bps",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    folds_frame.to_csv(
        output_root
        / "fold_crosscheck.csv",
        index=False,
    )

    summary_frame.to_csv(
        output_root
        / "summary.csv",
        index=False,
    )

    validated = (
        summary_frame.loc[
            summary_frame[
                "crosscheck_status"
            ]
            == "CROSS_ENGINE_VALIDATED"
        ]
    )

    validated.to_csv(
        output_root
        / "validated.csv",
        index=False,
    )

    audit = {
        "schema": (
            "pybroker_survivor_"
            "crosscheck_v1"
        ),
        "primary_timeframe": "1h",
        "input_survivors": int(
            len(
                survivors
            )
        ),
        "fold_count": int(
            len(
                folds
            )
        ),
        "validated": int(
            len(
                validated
            )
        ),
        "base_cost_bps_per_side": (
            args
            .base_cost_bps_per_side
        ),
        "stress_cost_bps_per_side": (
            args
            .stress_cost_bps_per_side
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "validation_mode": (
            "canonical_signal_schedule_"
            "replayed_in_pybroker"
        ),
        "warnings": [
            (
                "PyBroker independently "
                "validates scheduled execution "
                "and portfolio accounting; "
                "the canonical strategy engine "
                "still generates the signal "
                "schedule in V1."
            ),
            (
                "This is an independent "
                "cross-engine validation step, "
                "not execution authority."
            ),
        ],
    }

    (
        output_root
        / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "=" * 78
    )

    print(
        "PYBROKER CROSSCHECK"
    )

    print(
        "=" * 78
    )

    print(
        summary_frame.to_string(
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
