from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.integrations import (
    IntegrationRegistry,
    IntegrationRunner,
)
from stocks.research.panel import (
    build_relative_return_panel,
    center_cross_sectional_label,
    cross_sectional_rank_features,
    validate_panel_dataset,
)
from stocks.research.walkforward_splits import (
    rolling_periods,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


VARIANTS = {
    "BASE_RAW": {
        "timeframes": (),
        "representation": "raw",
    },
    "TACTICAL_RAW": {
        "timeframes": (
            "15m",
        ),
        "representation": "raw",
    },
    "SWING_RAW": {
        "timeframes": (
            "2h",
            "4h",
        ),
        "representation": "raw",
    },
    "TACTICAL_SWING_RAW": {
        "timeframes": (
            "15m",
            "2h",
            "4h",
        ),
        "representation": "raw",
    },
    "BASE_CSRANK": {
        "timeframes": (),
        "representation": "csrank",
    },
    "TACTICAL_SWING_CSRANK": {
        "timeframes": (
            "15m",
            "2h",
            "4h",
        ),
        "representation": "csrank",
    },
}


def load_frame(
    path: Path,
) -> pd.DataFrame:
    frame = pd.read_parquet(
        path
    )

    if isinstance(
        frame.index,
        pd.DatetimeIndex,
    ):
        result = frame.copy()

        result.index = pd.to_datetime(
            result.index,
            utc=True,
        )

        result.index.name = (
            "datetime"
        )

        return result.sort_index()

    for column in (
        "datetime",
        "timestamp",
        "timestamp_utc",
    ):
        if column not in frame:
            continue

        result = frame.copy()

        result[
            column
        ] = pd.to_datetime(
            result[
                column
            ],
            utc=True,
            errors="coerce",
        )

        return (
            result.dropna(
                subset=[
                    column
                ]
            )
            .set_index(
                column
            )
            .sort_index()
        )

    raise ValueError(
        f"{path}: timestamp missing"
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

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        f"{symbol}: 1h source missing"
    )


def alpha_columns(
    frame: pd.DataFrame,
) -> list[str]:
    excluded = {
        "label",
        "symbol",
        "vt_symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "vwap",
    }

    columns = []

    for column in frame.columns:
        if column in excluded:
            continue

        numeric = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        )

        if numeric.notna().any():
            columns.append(
                column
            )

    return columns


def context_columns(
    frame: pd.DataFrame,
    timeframes: tuple[
        str,
        ...,
    ],
) -> list[str]:
    columns = []

    for timeframe in timeframes:
        prefix = (
            f"{timeframe}_"
        )

        for column in frame.columns:
            if not column.startswith(
                prefix
            ):
                continue

            if column.endswith(
                "_source_bar_time"
            ):
                continue

            if column.endswith(
                "_availability_time"
            ):
                continue

            if column.endswith(
                "_age_minutes"
            ):
                continue

            numeric = pd.to_numeric(
                frame[
                    column
                ],
                errors="coerce",
            )

            if numeric.notna().any():
                columns.append(
                    column
                )

    return list(
        dict.fromkeys(
            columns
        )
    )


def alpha158(
    runner: IntegrationRunner,
    *,
    symbol: str,
    source: Path,
    raw: pd.DataFrame,
) -> pd.DataFrame:
    n = len(
        raw
    )

    train_end = int(
        n
        * 0.60
    )

    valid_end = int(
        n
        * 0.80
    )

    response = runner.run(
        "vnpy",
        "alpha158",
        {
            "input_parquet": str(
                source
            ),
            "symbol": symbol,
            "periods": {
                "train": [
                    str(
                        raw.index[
                            0
                        ]
                    ),
                    str(
                        raw.index[
                            train_end
                        ]
                    ),
                ],
                "valid": [
                    str(
                        raw.index[
                            train_end
                            + 1
                        ]
                    ),
                    str(
                        raw.index[
                            valid_end
                        ]
                    ),
                ],
                "test": [
                    str(
                        raw.index[
                            valid_end
                            + 1
                        ]
                    ),
                    str(
                        raw.index[
                            -1
                        ]
                    ),
                ],
            },
            "include_label": False,
            "vwap_policy": (
                "hlc3_proxy"
            ),
            "max_workers": 1,
        },
        timeout_seconds=900,
        raise_on_error=True,
    )

    return load_frame(
        Path(
            response
            .artifacts[
                0
            ]
            .path
        )
    )


def finite_values(
    rows: list[dict],
    key: str,
) -> list[float]:
    result = []

    for row in rows:
        value = row.get(
            key
        )

        if value is None:
            continue

        value = float(
            value
        )

        if math.isfinite(
            value
        ):
            result.append(
                value
            )

    return result


def summarize_folds(
    folds: list[dict],
) -> dict:
    rank_ic = finite_values(
        folds,
        "mean_rank_ic",
    )

    spread = finite_values(
        folds,
        "mean_top1_bottom1_label_spread",
    )

    pairwise = finite_values(
        folds,
        "mean_pairwise_rank_accuracy",
    )

    turnover = finite_values(
        folds,
        "top1_turnover_proxy",
    )

    return {
        "fold_count": len(
            folds
        ),
        "positive_fold_ratio": (
            float(
                np.mean(
                    [
                        value > 0.0
                        for value
                        in rank_ic
                    ]
                )
            )
            if rank_ic
            else None
        ),
        "median_mean_rank_ic": (
            float(
                np.median(
                    rank_ic
                )
            )
            if rank_ic
            else None
        ),
        "worst_mean_rank_ic": (
            float(
                min(
                    rank_ic
                )
            )
            if rank_ic
            else None
        ),
        "median_top1_bottom1_spread": (
            float(
                np.median(
                    spread
                )
            )
            if spread
            else None
        ),
        "median_pairwise_rank_accuracy": (
            float(
                np.median(
                    pairwise
                )
            )
            if pairwise
            else None
        ),
        "median_top1_turnover_proxy": (
            float(
                np.median(
                    turnover
                )
            )
            if turnover
            else None
        ),
    }


def classify(
    *,
    variant: str,
    summary: dict,
    delta_median: float,
    delta_worst: float,
) -> str:
    median_ic = float(
        summary[
            "median_mean_rank_ic"
        ]
    )

    worst_ic = float(
        summary[
            "worst_mean_rank_ic"
        ]
    )

    positive_ratio = float(
        summary[
            "positive_fold_ratio"
        ]
    )

    spread = float(
        summary[
            "median_top1_bottom1_spread"
        ]
    )

    pairwise = float(
        summary[
            "median_pairwise_rank_accuracy"
        ]
    )

    robust = (
        median_ic > 0.0
        and worst_ic > 0.0
        and positive_ratio >= 0.999
        and spread > 0.0
        and pairwise > 0.50
    )

    if variant.startswith(
        "BASE_"
    ):
        return (
            "PANEL_BASE_SURVIVOR"
            if robust
            else "PANEL_BASE_REJECT"
        )

    if (
        robust
        and delta_median > 0.0
        and delta_worst >= 0.0
    ):
        return (
            "PROMOTE_PANEL_CONTEXT"
        )

    if robust:
        return (
            "ROBUST_PANEL_CONTEXT"
        )

    if (
        median_ic > 0.0
        and positive_ratio
        >= (2.0 / 3.0)
        and spread > 0.0
    ):
        return (
            "PANEL_CHALLENGER"
        )

    return "REJECT"


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default=(
            "AAPL,AMD,MSFT,NVDA,QQQ"
        ),
    )

    parser.add_argument(
        "--benchmark",
        default="SPY",
    )

    parser.add_argument(
        "--hold-bars",
        default="21,42",
    )

    parser.add_argument(
        "--folds",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--min-assets",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--num-threads",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    symbols = [
        item.strip().upper()
        for item
        in args.symbols.split(
            ","
        )
        if item.strip()
    ]

    benchmark_symbol = (
        args.benchmark
        .strip()
        .upper()
    )

    if benchmark_symbol in symbols:
        raise ValueError(
            "benchmark must not be "
            "a trainable panel asset"
        )

    if len(
        set(
            symbols
        )
    ) != len(
        symbols
    ):
        raise ValueError(
            "duplicate panel symbols"
        )

    min_assets = (
        args.min_assets
        if args.min_assets > 0
        else len(
            symbols
        )
    )

    if (
        min_assets
        > len(
            symbols
        )
    ):
        raise ValueError(
            "min_assets exceeds "
            "panel size"
        )

    hold_bars_values = [
        int(
            item.strip()
        )
        for item
        in args.hold_bars.split(
            ","
        )
        if item.strip()
    ]

    registry = (
        IntegrationRegistry.load(
            ROOT
            / "config"
            / "integrations.yaml",
            project_root=ROOT,
        )
    )

    runner = IntegrationRunner(
        registry
    )

    raw_frames = {}

    prepared = {}

    alpha_feature_map = {}

    tactical_start = {}

    full_context_map = {}

    for symbol in symbols:
        source = one_hour_source(
            symbol
        )

        raw = load_frame(
            source
        )

        raw_frames[
            symbol
        ] = raw

        alpha = alpha158(
            runner,
            symbol=symbol,
            source=source,
            raw=raw,
        )

        alpha_features = (
            alpha_columns(
                alpha
            )
        )

        alpha_feature_map[
            symbol
        ] = alpha_features

        mtf_path = (
            ROOT
            / "artifacts"
            / "research_runtime"
            / "mtf"
            / f"{symbol}_mtf.parquet"
        )

        if not mtf_path.is_file():
            raise FileNotFoundError(
                mtf_path
            )

        mtf = pd.read_parquet(
            mtf_path
        )

        mtf[
            "decision_time"
        ] = pd.to_datetime(
            mtf[
                "decision_time"
            ],
            utc=True,
        )

        mtf[
            "decision_bar_time"
        ] = pd.to_datetime(
            mtf[
                "decision_bar_time"
            ],
            utc=True,
        )

        available = mtf.loc[
            mtf[
                "15m_available"
            ]
            == 1,
            "decision_bar_time",
        ]

        if available.empty:
            raise ValueError(
                f"{symbol}: no causal "
                "15m history"
            )

        tactical_start[
            symbol
        ] = available.min()

        full_context = (
            context_columns(
                mtf,
                (
                    "15m",
                    "2h",
                    "4h",
                ),
            )
        )

        full_context_map[
            symbol
        ] = full_context

        mtf_by_bar = mtf[
            [
                "decision_bar_time",
                "decision_time",
                *full_context,
            ]
        ].copy()

        mtf_by_bar = (
            mtf_by_bar
            .set_index(
                "decision_bar_time"
            )
            .sort_index()
        )

        feature_frame = (
            alpha[
                alpha_features
            ]
            .join(
                mtf_by_bar,
                how="inner",
            )
        )

        feature_frame.index.name = (
            "decision_bar_time"
        )

        feature_frame = (
            feature_frame.reset_index()
        )

        feature_frame[
            "symbol"
        ] = symbol

        prepared[
            symbol
        ] = feature_frame

    first_symbol = symbols[
        0
    ]

    alpha_features = (
        alpha_feature_map[
            first_symbol
        ]
    )

    alpha_reference_set = set(
        alpha_features
    )

    for symbol in symbols[
        1:
    ]:
        if (
            set(
                alpha_feature_map[
                    symbol
                ]
            )
            != alpha_reference_set
        ):
            raise ValueError(
                f"{symbol}: Alpha158 "
                "feature schema differs"
            )

    if len(
        alpha_features
    ) < 150:
        raise ValueError(
            "unexpectedly small "
            "Alpha158 feature set"
        )

    full_context = (
        full_context_map[
            first_symbol
        ]
    )

    context_reference_set = set(
        full_context
    )

    for symbol in symbols[
        1:
    ]:
        if (
            set(
                full_context_map[
                    symbol
                ]
            )
            != context_reference_set
        ):
            raise ValueError(
                f"{symbol}: MTF context "
                "schema differs"
            )

    benchmark_frame = load_frame(
        one_hour_source(
            benchmark_symbol
        )
    )

    feature_panel = pd.concat(
        [
            prepared[
                symbol
            ]
            for symbol
            in symbols
        ],
        ignore_index=True,
    )

    common_start = max(
        tactical_start.values()
    )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "panel"
    )

    input_root = (
        output_root
        / "inputs"
    )

    input_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for hold_bars in (
        hold_bars_values
    ):
        returns = (
            build_relative_return_panel(
                raw_frames,
                benchmark_frame,
                hold_bars=hold_bars,
            )
        )

        panel = feature_panel.merge(
            returns,
            on=[
                "decision_bar_time",
                "symbol",
            ],
            how="inner",
            validate="one_to_one",
        )

        panel = panel.loc[
            panel[
                "decision_bar_time"
            ]
            >= common_start
        ].copy()

        panel = (
            center_cross_sectional_label(
                panel,
                time_column=(
                    "decision_time"
                ),
                min_assets=min_assets,
            )
        )

        panel_audit = (
            validate_panel_dataset(
                panel.rename(
                    columns={
                        "decision_time": (
                            "datetime"
                        ),
                    }
                ),
                min_assets=min_assets,
            )
        )

        unique_times = (
            pd.DatetimeIndex(
                panel[
                    "decision_time"
                ]
                .drop_duplicates()
                .sort_values()
            )
        )

        periods = rolling_periods(
            unique_times,
            hold_bars=hold_bars,
            requested_folds=(
                args.folds
            ),
        )

        variant_results = []

        for (
            variant,
            specification,
        ) in VARIANTS.items():
            timeframes = tuple(
                specification[
                    "timeframes"
                ]
            )

            representation = str(
                specification[
                    "representation"
                ]
            )

            context = (
                context_columns(
                    panel,
                    timeframes,
                )
            )

            features = [
                *alpha_features,
                *context,
            ]

            dataset = panel.copy()

            if (
                representation
                == "csrank"
            ):
                passthrough = [
                    column
                    for column
                    in features
                    if column.endswith(
                        "_available"
                    )
                ]

                dataset = (
                    cross_sectional_rank_features(
                        dataset,
                        time_column=(
                            "decision_time"
                        ),
                        feature_columns=(
                            features
                        ),
                        passthrough_columns=(
                            passthrough
                        ),
                    )
                )

            dataset = dataset[
                [
                    "decision_time",
                    "symbol",
                    *features,
                    "label",
                    "raw_return",
                    "benchmark_return",
                    "excess_return",
                    "cross_section_size",
                ]
            ].copy()

            dataset = dataset.rename(
                columns={
                    "decision_time": (
                        "datetime"
                    ),
                }
            )

            dataset_path = (
                input_root
                / (
                    f"hold{hold_bars}_"
                    f"{variant.lower()}"
                    ".parquet"
                )
            )

            dataset.to_parquet(
                dataset_path,
                index=False,
            )

            fold_results = []

            for fold_index, period in (
                enumerate(
                    periods,
                    start=1,
                )
            ):
                response = runner.run(
                    "qlib",
                    "fit_predict_panel_lgbm",
                    {
                        "input_parquet": str(
                            dataset_path
                        ),
                        "feature_columns": (
                            features
                        ),
                        "periods": period,
                        "preserve_feature_missingness": (
                            True
                        ),
                        "min_cross_section": (
                            min_assets
                        ),
                        "target_kind": (
                            "cross_section_centered_"
                            "spy_excess_return"
                        ),
                        "label_semantics": (
                            "signal close[t]; "
                            "entry open[t+1]; "
                            f"exit close[t+{hold_bars}]; "
                            f"minus {benchmark_symbol} "
                            "same-horizon return; "
                            "cross-section centered "
                            "at decision_time"
                        ),
                        "feature_representation": (
                            representation
                        ),
                        "seed": (
                            3000
                            + fold_index
                        ),
                        "num_boost_round": 800,
                        "early_stopping_rounds": 40,
                        "learning_rate": 0.025,
                        "num_leaves": 31,
                        "num_threads": (
                            args.num_threads
                        ),
                    },
                    timeout_seconds=1200,
                    raise_on_error=True,
                )

                metrics = dict(
                    response.data
                )

                fold_results.append(
                    {
                        "fold": (
                            fold_index
                        ),
                        **metrics,
                    }
                )

                print()
                print(
                    "PANEL",
                    hold_bars,
                    variant,
                    "FOLD",
                    fold_index,
                )

                print(
                    "MEAN_RANK_IC",
                    metrics.get(
                        "mean_rank_ic"
                    ),
                )

                print(
                    "PAIRWISE",
                    metrics.get(
                        "mean_pairwise_rank_accuracy"
                    ),
                )

                print(
                    "TOP1_BOTTOM1",
                    metrics.get(
                        "mean_top1_bottom1_label_spread"
                    ),
                )

                print(
                    "TOP1_TURNOVER",
                    metrics.get(
                        "top1_turnover_proxy"
                    ),
                )

            summary = (
                summarize_folds(
                    fold_results
                )
            )

            variant_results.append(
                {
                    "variant": variant,
                    "timeframes": list(
                        timeframes
                    ),
                    "representation": (
                        representation
                    ),
                    "feature_count": len(
                        features
                    ),
                    **summary,
                    "folds": (
                        fold_results
                    ),
                }
            )

        by_name = {
            item[
                "variant"
            ]: item
            for item
            in variant_results
        }

        for item in variant_results:
            representation = item[
                "representation"
            ]

            base_name = (
                "BASE_CSRANK"
                if representation
                == "csrank"
                else "BASE_RAW"
            )

            base = by_name[
                base_name
            ]

            delta_median = (
                float(
                    item[
                        "median_mean_rank_ic"
                    ]
                )
                - float(
                    base[
                        "median_mean_rank_ic"
                    ]
                )
            )

            delta_worst = (
                float(
                    item[
                        "worst_mean_rank_ic"
                    ]
                )
                - float(
                    base[
                        "worst_mean_rank_ic"
                    ]
                )
            )

            item[
                "delta_median_rank_ic_vs_base"
            ] = delta_median

            item[
                "delta_worst_rank_ic_vs_base"
            ] = delta_worst

            item[
                "status"
            ] = classify(
                variant=item[
                    "variant"
                ],
                summary=item,
                delta_median=(
                    delta_median
                ),
                delta_worst=(
                    delta_worst
                ),
            )

        print()
        print(
            "=" * 78
        )

        print(
            "PANEL SUMMARY HOLD",
            hold_bars,
        )

        for item in variant_results:
            print(
                item[
                    "variant"
                ],
                item[
                    "status"
                ],
                "MEDIAN_MEAN_IC=",
                item[
                    "median_mean_rank_ic"
                ],
                "WORST=",
                item[
                    "worst_mean_rank_ic"
                ],
                "SPREAD=",
                item[
                    "median_top1_bottom1_spread"
                ],
            )

        results.append(
            {
                "hold_bars": (
                    hold_bars
                ),
                "panel_audit": (
                    panel_audit
                ),
                "common_start": str(
                    common_start
                ),
                "time_group_count": int(
                    len(
                        unique_times
                    )
                ),
                "fold_count": len(
                    periods
                ),
                "variants": (
                    variant_results
                ),
            }
        )

    artifact = (
        output_root
        / "panel_qlib_ablation.json"
    )

    payload = {
        "schema": (
            "panel_qlib_ablation_v1"
        ),
        "symbols": symbols,
        "benchmark": (
            benchmark_symbol
        ),
        "target": (
            "cross-section centered "
            "same-horizon benchmark "
            "excess return"
        ),
        "results": results,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    artifact.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    summary_rows = []

    for result in results:
        for variant in (
            result[
                "variants"
            ]
        ):
            summary_rows.append(
                {
                    "hold_bars": (
                        result[
                            "hold_bars"
                        ]
                    ),
                    "variant": (
                        variant[
                            "variant"
                        ]
                    ),
                    "status": (
                        variant[
                            "status"
                        ]
                    ),
                    "feature_count": (
                        variant[
                            "feature_count"
                        ]
                    ),
                    "median_mean_rank_ic": (
                        variant[
                            "median_mean_rank_ic"
                        ]
                    ),
                    "worst_mean_rank_ic": (
                        variant[
                            "worst_mean_rank_ic"
                        ]
                    ),
                    "positive_fold_ratio": (
                        variant[
                            "positive_fold_ratio"
                        ]
                    ),
                    "median_top1_bottom1_spread": (
                        variant[
                            "median_top1_bottom1_spread"
                        ]
                    ),
                    "median_pairwise_rank_accuracy": (
                        variant[
                            "median_pairwise_rank_accuracy"
                        ]
                    ),
                    "delta_median_rank_ic_vs_base": (
                        variant[
                            "delta_median_rank_ic_vs_base"
                        ]
                    ),
                    "delta_worst_rank_ic_vs_base": (
                        variant[
                            "delta_worst_rank_ic_vs_base"
                        ]
                    ),
                }
            )

    summary_path = (
        output_root
        / "panel_qlib_ablation_summary.csv"
    )

    pd.DataFrame(
        summary_rows
    ).to_csv(
        summary_path,
        index=False,
    )

    print()
    print(
        "ARTIFACT",
        artifact,
    )

    print(
        "SUMMARY",
        summary_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
