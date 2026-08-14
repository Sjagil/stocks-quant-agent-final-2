#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.strategy_factory_1h import (
    build_feature_caches,
    eligible_1h_specs,
    evaluate_hypothesis,
    generate_hypotheses,
    hypotheses_frame,
    period_metrics,
    prepare_one_hour_frame,
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


def parse_symbols(
    value: str,
) -> tuple[str, ...]:
    result = []

    for raw in (
        value.split(",")
    ):
        symbol = (
            raw.strip()
            .upper()
        )

        if (
            symbol
            and symbol
            not in result
        ):
            result.append(
                symbol
            )

    if not result:
        raise ValueError(
            "no symbols supplied"
        )

    return tuple(
        result
    )


def parse_names(
    value: str | None,
) -> set[str] | None:
    if not value:
        return None

    result = {
        item.strip()
        for item
        in value.split(",")
        if item.strip()
    }

    return (
        result
        or None
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

    for candidate in (
        candidates
    ):
        if (
            candidate.is_file()
        ):
            return (
                candidate
            )

    raise FileNotFoundError(
        f"{symbol}: 1h source missing"
    )


def load_frames(
    symbols: tuple[
        str,
        ...,
    ],
) -> tuple[
    dict[
        str,
        pd.DataFrame,
    ],
    dict[
        str,
        str,
    ],
]:
    frames = {}
    paths = {}

    for symbol in (
        symbols
    ):
        path = (
            one_hour_source(
                symbol
            )
        )

        raw = (
            pd.read_parquet(
                path
            )
        )

        frame = (
            prepare_one_hour_frame(
                raw,
                symbol,
            )
        )

        if (
            len(frame)
            < 4000
        ):
            raise ValueError(
                f"{symbol}: fewer than "
                "4000 causal 1h bars"
            )

        frames[
            symbol
        ] = frame

        paths[
            symbol
        ] = str(
            path
        )

        print(
            symbol,
            "1H_ROWS",
            len(frame),
            "FIRST",
            frame[
                "date"
            ].min(),
            "LAST",
            frame[
                "date"
            ].max(),
        )

    return (
        frames,
        paths,
    )


def expanded_metrics(
    prefix: str,
    metrics: dict,
) -> dict:
    return {
        f"{prefix}_{key}": value
        for key, value
        in metrics.items()
    }


def finite_positive(
    value,
) -> bool:
    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return (
        math.isfinite(
            result
        )
        and result > 0
    )


def main() -> int:
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--symbols",
        default=",".join(
            DEFAULT_SYMBOLS
        ),
    )

    parser.add_argument(
        "--strategies",
        default=None,
    )

    parser.add_argument(
        "--max-variants-per-strategy",
        type=int,
        default=24,
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
        "--top-per-family",
        type=int,
        default=2,
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
        "--min-train-trades",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--min-valid-trades",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--min-test-trades",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20260814,
    )

    args = (
        parser.parse_args()
    )

    symbols = parse_symbols(
        args.symbols
    )

    strategy_filter = (
        parse_names(
            args.strategies
        )
    )

    frames, sources = (
        load_frames(
            symbols
        )
    )

    anchor = (
        "SPY"
        if "SPY" in frames
        else symbols[0]
    )

    anchor_index = (
        pd.DatetimeIndex(
            frames[
                anchor
            ][
                "date"
            ]
        )
        .sort_values()
        .drop_duplicates()
    )

    folds = rolling_periods(
        anchor_index,
        hold_bars=(
            int(
                args.purge_bars
            )
        ),
        requested_folds=(
            int(
                args.folds
            )
        ),
    )

    hypotheses = (
        generate_hypotheses(
            max_variants_per_strategy=(
                args
                .max_variants_per_strategy
            ),
            seed=args.seed,
        )
    )

    if (
        strategy_filter
        is not None
    ):
        hypotheses = [
            hypothesis
            for hypothesis
            in hypotheses
            if (
                hypothesis.strategy
                in strategy_filter
            )
        ]

    if not hypotheses:
        raise ValueError(
            "no hypotheses selected"
        )

    spec_map = {
        spec.name: spec
        for spec in (
            eligible_1h_specs()
        )
    }

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "strategy_factory_1h"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    hypothesis_table = (
        hypotheses_frame(
            hypotheses
        )
    )

    hypothesis_table.to_parquet(
        output_root
        / "hypotheses.parquet",
        index=False,
    )

    print()
    print(
        "PRIMARY_TIMEFRAME",
        "1h",
    )

    print(
        "HYPOTHESES",
        len(
            hypotheses
        ),
    )

    print(
        "FOLDS",
        len(
            folds
        ),
    )

    trade_cache = {}

    failures = []

    by_strategy = {}

    for hypothesis in (
        hypotheses
    ):
        by_strategy.setdefault(
            hypothesis.strategy,
            [],
        ).append(
            hypothesis
        )

    for (
        strategy_name,
        strategy_hypotheses,
    ) in sorted(
        by_strategy.items()
    ):
        print()
        print(
            "EVALUATE",
            strategy_name,
            "VARIANTS",
            len(
                strategy_hypotheses
            ),
        )

        spec = (
            spec_map[
                strategy_name
            ]
        )

        caches = (
            build_feature_caches(
                frames
            )
        )

        for hypothesis in (
            strategy_hypotheses
        ):
            try:
                trades = (
                    evaluate_hypothesis(
                        hypothesis,
                        spec,
                        frames,
                        caches,
                    )
                )

                trade_cache[
                    hypothesis
                    .hypothesis_id
                ] = trades

            except Exception as exc:
                failures.append(
                    {
                        "hypothesis_id": (
                            hypothesis
                            .hypothesis_id
                        ),
                        "strategy": (
                            hypothesis
                            .strategy
                        ),
                        "error": (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    }
                )

                trade_cache[
                    hypothesis
                    .hypothesis_id
                ] = pd.DataFrame()

        del caches

    candidate_rows = []
    selected_rows = []

    for (
        fold_number,
        periods,
    ) in enumerate(
        folds,
        start=1,
    ):
        print()
        print(
            "FOLD",
            fold_number,
        )

        fold_candidates = []

        for hypothesis in (
            hypotheses
        ):
            trades = (
                trade_cache[
                    hypothesis
                    .hypothesis_id
                ]
            )

            train = (
                period_metrics(
                    trades,
                    periods[
                        "train"
                    ],
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            valid = (
                period_metrics(
                    trades,
                    periods[
                        "valid"
                    ],
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            valid_stress = (
                period_metrics(
                    trades,
                    periods[
                        "valid"
                    ],
                    cost_bps_per_side=(
                        args
                        .stress_cost_bps_per_side
                    ),
                )
            )

            train_pf = (
                train[
                    "profit_factor"
                ]
            )

            valid_pf = (
                valid[
                    "profit_factor"
                ]
            )

            gate_pass = (
                train[
                    "trades"
                ]
                >= args.min_train_trades
                and valid[
                    "trades"
                ]
                >= args.min_valid_trades
                and finite_positive(
                    train[
                        "net_expectancy"
                    ]
                )
                and finite_positive(
                    valid[
                        "net_expectancy"
                    ]
                )
                and finite_positive(
                    valid_stress[
                        "net_expectancy"
                    ]
                )
                and (
                    train_pf
                    > 1.0
                )
                and (
                    valid_pf
                    > 1.0
                )
            )

            robust_expectancy = (
                min(
                    train[
                        "net_expectancy_bps"
                    ],
                    valid[
                        "net_expectancy_bps"
                    ],
                )
                if (
                    math.isfinite(
                        train[
                            "net_expectancy_bps"
                        ]
                    )
                    and math.isfinite(
                        valid[
                            "net_expectancy_bps"
                        ]
                    )
                )
                else -math.inf
            )

            robust_pf = (
                min(
                    train_pf,
                    valid_pf,
                )
                if (
                    not pd.isna(
                        train_pf
                    )
                    and not pd.isna(
                        valid_pf
                    )
                )
                else -math.inf
            )

            row = {
                "fold": (
                    fold_number
                ),
                "hypothesis_id": (
                    hypothesis
                    .hypothesis_id
                ),
                "strategy": (
                    hypothesis
                    .strategy
                ),
                "family": (
                    hypothesis
                    .family
                ),
                "horizon": (
                    hypothesis
                    .horizon
                ),
                "parameter_basis": (
                    hypothesis
                    .parameter_basis
                ),
                "params_json": (
                    json.dumps(
                        hypothesis.params,
                        sort_keys=True,
                        separators=(
                            ",",
                            ":",
                        ),
                        default=str,
                    )
                ),
                "gate_pass": bool(
                    gate_pass
                ),
                "robust_expectancy_bps": (
                    robust_expectancy
                ),
                "robust_profit_factor": (
                    robust_pf
                ),
                **expanded_metrics(
                    "train",
                    train,
                ),
                **expanded_metrics(
                    "valid",
                    valid,
                ),
                **expanded_metrics(
                    "valid_stress",
                    valid_stress,
                ),
            }

            fold_candidates.append(
                row
            )

        fold_frame = (
            pd.DataFrame(
                fold_candidates
            )
        )

        candidate_rows.extend(
            fold_candidates
        )

        passed = (
            fold_frame.loc[
                fold_frame[
                    "gate_pass"
                ]
            ]
            .sort_values(
                [
                    "family",
                    "robust_expectancy_bps",
                    "robust_profit_factor",
                    "valid_trades",
                ],
                ascending=[
                    True,
                    False,
                    False,
                    False,
                ],
            )
            .groupby(
                "family",
                sort=False,
            )
            .head(
                args.top_per_family
            )
        )

        print(
            "CANDIDATES",
            int(
                fold_frame[
                    "gate_pass"
                ].sum()
            ),
            "SELECTED",
            len(
                passed
            ),
        )

        for _, selected in (
            passed.iterrows()
        ):
            hypothesis_id = (
                selected[
                    "hypothesis_id"
                ]
            )

            trades = (
                trade_cache[
                    hypothesis_id
                ]
            )

            test = (
                period_metrics(
                    trades,
                    periods[
                        "test"
                    ],
                    cost_bps_per_side=(
                        args
                        .base_cost_bps_per_side
                    ),
                )
            )

            test_stress = (
                period_metrics(
                    trades,
                    periods[
                        "test"
                    ],
                    cost_bps_per_side=(
                        args
                        .stress_cost_bps_per_side
                    ),
                )
            )

            output = (
                selected.to_dict()
            )

            output.update(
                expanded_metrics(
                    "test",
                    test,
                )
            )

            output.update(
                expanded_metrics(
                    "test_stress",
                    test_stress,
                )
            )

            output[
                "test_usable"
            ] = (
                test[
                    "trades"
                ]
                >= args.min_test_trades
            )

            selected_rows.append(
                output
            )

    candidates = (
        pd.DataFrame(
            candidate_rows
        )
    )

    selected = (
        pd.DataFrame(
            selected_rows
        )
    )

    candidates.to_csv(
        output_root
        / "fold_candidates.csv",
        index=False,
    )

    selected.to_csv(
        output_root
        / "fold_selected.csv",
        index=False,
    )

    aggregate_rows = []

    if not selected.empty:
        for (
            hypothesis_id,
            group,
        ) in selected.groupby(
            "hypothesis_id"
        ):
            usable = group.loc[
                group[
                    "test_usable"
                ]
            ]

            if usable.empty:
                evaluated_folds = 0
                positive_ratio = 0.0
                stress_positive_ratio = (
                    0.0
                )
                median_expectancy = (
                    math.nan
                )
                worst_expectancy = (
                    math.nan
                )
                median_stress = (
                    math.nan
                )
                median_pf = (
                    math.nan
                )
                total_test_trades = 0
            else:
                evaluated_folds = (
                    len(
                        usable
                    )
                )

                positive_ratio = float(
                    (
                        usable[
                            "test_net_expectancy"
                        ]
                        > 0
                    )
                    .mean()
                )

                stress_positive_ratio = float(
                    (
                        usable[
                            "test_stress_net_expectancy"
                        ]
                        > 0
                    )
                    .mean()
                )

                median_expectancy = float(
                    usable[
                        "test_net_expectancy_bps"
                    ]
                    .median()
                )

                worst_expectancy = float(
                    usable[
                        "test_net_expectancy_bps"
                    ]
                    .min()
                )

                median_stress = float(
                    usable[
                        "test_stress_net_expectancy_bps"
                    ]
                    .median()
                )

                median_pf = float(
                    usable[
                        "test_profit_factor"
                    ]
                    .median()
                )

                total_test_trades = int(
                    usable[
                        "test_trades"
                    ]
                    .sum()
                )

            selected_folds = (
                len(
                    group
                )
            )

            selection_frequency = (
                selected_folds
                / max(
                    len(folds),
                    1,
                )
            )

            strong = (
                evaluated_folds >= 3
                and selection_frequency
                >= 0.75
                and positive_ratio
                == 1.0
                and stress_positive_ratio
                == 1.0
                and median_expectancy
                > 0
                and worst_expectancy
                > 0
                and median_stress
                > 0
                and median_pf
                >= 1.25
            )

            provisional = (
                evaluated_folds >= 2
                and selection_frequency
                >= 0.50
                and positive_ratio
                == 1.0
                and stress_positive_ratio
                == 1.0
                and median_expectancy
                > 0
                and worst_expectancy
                > 0
                and median_stress
                > 0
                and median_pf
                > 1.10
            )

            survivor = (
                evaluated_folds >= 3
                and selection_frequency
                >= 0.75
                and positive_ratio
                >= 0.75
                and stress_positive_ratio
                >= 0.75
                and median_expectancy
                > 0
                and median_stress
                > 0
                and median_pf
                > 1.10
            )

            if strong:
                status = (
                    "STRONG_SURVIVOR"
                )
            elif provisional:
                status = (
                    "PROVISIONAL_SURVIVOR"
                )
            elif survivor:
                status = (
                    "SURVIVOR"
                )
            else:
                status = (
                    "REJECT"
                )

            first = (
                group.iloc[
                    0
                ]
            )

            aggregate_rows.append(
                {
                    "hypothesis_id": (
                        hypothesis_id
                    ),
                    "strategy": (
                        first[
                            "strategy"
                        ]
                    ),
                    "family": (
                        first[
                            "family"
                        ]
                    ),
                    "horizon": (
                        first[
                            "horizon"
                        ]
                    ),
                    "parameter_basis": (
                        first[
                            "parameter_basis"
                        ]
                    ),
                    "params_json": (
                        first[
                            "params_json"
                        ]
                    ),
                    "selected_folds": (
                        selected_folds
                    ),
                    "selection_frequency": (
                        selection_frequency
                    ),
                    "evaluated_test_folds": (
                        evaluated_folds
                    ),
                    "positive_test_fold_ratio": (
                        positive_ratio
                    ),
                    "stress_positive_test_fold_ratio": (
                        stress_positive_ratio
                    ),
                    "median_test_expectancy_bps": (
                        median_expectancy
                    ),
                    "worst_test_expectancy_bps": (
                        worst_expectancy
                    ),
                    "median_stress_test_expectancy_bps": (
                        median_stress
                    ),
                    "median_test_profit_factor": (
                        median_pf
                    ),
                    "total_test_trades": (
                        total_test_trades
                    ),
                    "status": status,
                }
            )

    aggregate = (
        pd.DataFrame(
            aggregate_rows
        )
    )

    base_summary = (
        hypothesis_table.copy()
    )

    if aggregate.empty:
        summary = (
            base_summary.copy()
        )

        summary[
            "selected_folds"
        ] = 0

        summary[
            "status"
        ] = (
            "REJECT_NOT_SELECTED"
        )
    else:
        merge_columns = [
            column
            for column
            in aggregate.columns
            if column
            not in {
                "strategy",
                "family",
                "horizon",
                "parameter_basis",
                "params_json",
            }
        ]

        summary = (
            base_summary.merge(
                aggregate[
                    merge_columns
                ],
                on="hypothesis_id",
                how="left",
            )
        )

        summary[
            "selected_folds"
        ] = (
            summary[
                "selected_folds"
            ]
            .fillna(
                0
            )
            .astype(
                int
            )
        )

        summary[
            "status"
        ] = (
            summary[
                "status"
            ]
            .fillna(
                "REJECT_NOT_SELECTED"
            )
        )

    survivor_mask = (
        summary[
            "status"
        ]
        .isin(
            [
                "SURVIVOR",
                "PROVISIONAL_SURVIVOR",
                "STRONG_SURVIVOR",
            ]
        )
    )

    survivors = (
        summary.loc[
            survivor_mask
        ]
        .sort_values(
            [
                "status",
                "median_test_expectancy_bps",
                "median_test_profit_factor",
            ],
            ascending=[
                True,
                False,
                False,
            ],
        )
    )

    rejected = (
        summary.loc[
            ~survivor_mask
        ]
    )

    summary.to_csv(
        output_root
        / "all_hypotheses_summary.csv",
        index=False,
    )

    survivors.to_csv(
        output_root
        / "survivors.csv",
        index=False,
    )

    rejected.to_csv(
        output_root
        / "rejected.csv",
        index=False,
    )

    survivor_payload = (
        json.loads(
            survivors.to_json(
                orient="records"
            )
        )
        if not survivors.empty
        else []
    )

    (
        output_root
        / "survivors.json"
    ).write_text(
        json.dumps(
            survivor_payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    family_rows = []

    for (
        family,
        group,
    ) in (
        summary.groupby(
            "family"
        )
    ):
        selected_group = (
            group.loc[
                group[
                    "selected_folds"
                ]
                > 0
            ]
        )

        survivor_group = (
            group.loc[
                group[
                    "status"
                ]
                .isin(
                    [
                        "SURVIVOR",
                        "PROVISIONAL_SURVIVOR",
                        "STRONG_SURVIVOR",
                    ]
                )
            ]
        )

        values = (
            pd.to_numeric(
                selected_group.get(
                    "median_test_expectancy_bps",
                    pd.Series(
                        dtype=float
                    ),
                ),
                errors="coerce",
            )
        )

        finite_values = (
            values.loc[
                np.isfinite(
                    values
                )
            ]
        )

        family_rows.append(
            {
                "family": family,
                "generated_hypotheses": (
                    len(
                        group
                    )
                ),
                "selected_hypotheses": (
                    len(
                        selected_group
                    )
                ),
                "survivors": (
                    len(
                        survivor_group
                    )
                ),
                "best_median_test_expectancy_bps": (
                    float(
                        finite_values.max()
                    )
                    if not finite_values.empty
                    else math.nan
                ),
            }
        )

    family = (
        pd.DataFrame(
            family_rows
        )
        .sort_values(
            [
                "survivors",
                "best_median_test_expectancy_bps",
            ],
            ascending=[
                False,
                False,
            ],
        )
    )

    family.to_csv(
        output_root
        / "family_leaderboard.csv",
        index=False,
    )

    survivor_trade_rows = []

    survivor_ids = set(
        survivors[
            "hypothesis_id"
        ].tolist()
    )

    for hypothesis in (
        hypotheses
    ):
        if (
            hypothesis
            .hypothesis_id
            not in survivor_ids
        ):
            continue

        trades = (
            trade_cache[
                hypothesis
                .hypothesis_id
            ]
        )

        if trades.empty:
            continue

        survivor_trade_rows.append(
            trades
        )

    if survivor_trade_rows:
        survivor_trades = (
            pd.concat(
                survivor_trade_rows,
                ignore_index=True,
            )
        )

        survivor_trades.to_parquet(
            output_root
            / "survivor_trades.parquet",
            index=False,
        )

    audit = {
        "schema": (
            "strategy_factory_1h_v1"
        ),
        "primary_timeframe": (
            "1h"
        ),
        "parameter_basis": (
            "BAR_NATIVE_1H"
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "symbols": list(
            symbols
        ),
        "anchor_symbol": (
            anchor
        ),
        "sources": sources,
        "generated_hypotheses": (
            len(
                hypotheses
            )
        ),
        "strategy_count": (
            len(
                {
                    hypothesis.strategy
                    for hypothesis
                    in hypotheses
                }
            )
        ),
        "family_count": (
            len(
                {
                    hypothesis.family
                    for hypothesis
                    in hypotheses
                }
            )
        ),
        "fold_count": (
            len(
                folds
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
        "survivor_count": (
            len(
                survivors
            )
        ),
        "strong_survivor_count": int(
            (
                survivors[
                    "status"
                ]
                == "STRONG_SURVIVOR"
            ).sum()
        )
        if not survivors.empty
        else 0,
        "failures": failures,
        "warnings": [
            (
                "1h is the primary signal "
                "and decision timeframe."
            ),
            (
                "Parameters are interpreted "
                "as BAR_NATIVE_1H in this "
                "version."
            ),
            (
                "Trades are required to be "
                "fully contained within each "
                "walk-forward segment."
            ),
            (
                "Trade observations can overlap "
                "across assets and holding "
                "intervals; these are research "
                "selection metrics, not "
                "independent statistical "
                "observations."
            ),
            (
                "No portfolio equity curve is "
                "inferred from overlapping "
                "single-strategy trades."
            ),
            (
                "No strategy, model or donor "
                "has broker authority."
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
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "=" * 80
    )

    print(
        "1H STRATEGY FACTORY"
    )

    print(
        "=" * 80
    )

    print(
        "HYPOTHESES",
        len(
            hypotheses
        ),
    )

    print(
        "SURVIVORS",
        len(
            survivors
        ),
    )

    if not survivors.empty:
        columns = [
            "strategy",
            "family",
            "status",
            "selected_folds",
            "evaluated_test_folds",
            "positive_test_fold_ratio",
            "median_test_expectancy_bps",
            "worst_test_expectancy_bps",
            "median_stress_test_expectancy_bps",
            "median_test_profit_factor",
            "total_test_trades",
        ]

        print()
        print(
            survivors[
                columns
            ]
            .head(
                30
            )
            .to_string(
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
