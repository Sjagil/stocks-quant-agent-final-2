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
from stocks.research.swing_labels import (
    forward_open_to_close_return,
)


ROOT = Path(
    __file__
).resolve().parents[1]


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
        frame = frame.copy()

        frame.index = pd.to_datetime(
            frame.index,
            utc=True,
        )

        frame.index.name = "datetime"

        return frame.sort_index()

    for column in (
        "datetime",
        "timestamp",
        "timestamp_utc",
    ):
        if column not in frame:
            continue

        frame = frame.copy()

        frame[column] = pd.to_datetime(
            frame[column],
            utc=True,
            errors="coerce",
        )

        frame = (
            frame.dropna(
                subset=[column]
            )
            .set_index(column)
            .sort_index()
        )

        frame.index.name = "datetime"

        return frame

    raise ValueError(
        f"{path}: no timestamp"
    )


def basic_periods(
    index: pd.DatetimeIndex,
) -> dict[str, list[str]]:
    n = len(index)

    if n < 1000:
        raise ValueError(
            "not enough data"
        )

    first = int(
        n * 0.60
    )

    second = int(
        n * 0.80
    )

    return {
        "train": [
            str(index[0]),
            str(index[first - 1]),
        ],
        "valid": [
            str(index[first]),
            str(index[second - 1]),
        ],
        "test": [
            str(index[second]),
            str(index[-1]),
        ],
    }


def rolling_periods(
    index: pd.DatetimeIndex,
    *,
    hold_bars: int,
    requested_folds: int,
) -> list[dict[str, list[str]]]:
    index = pd.DatetimeIndex(
        index
    ).sort_values()

    n = len(index)

    if n < 4000:
        raise ValueError(
            "at least 4000 rows required"
        )

    gap = (
        hold_bars + 1
    )

    valid_len = max(
        500,
        int(n * 0.10),
    )

    test_len = max(
        500,
        int(n * 0.10),
    )

    initial_train_end = (
        int(n * 0.45)
        - 1
    )

    folds = []

    for fold_number in range(
        requested_folds
    ):
        train_end = (
            initial_train_end
            + fold_number
            * test_len
        )

        valid_start = (
            train_end
            + gap
            + 1
        )

        valid_end = (
            valid_start
            + valid_len
            - 1
        )

        test_start = (
            valid_end
            + gap
            + 1
        )

        test_end = (
            test_start
            + test_len
            - 1
        )

        if test_end >= n:
            break

        folds.append(
            {
                "train": [
                    str(index[0]),
                    str(index[train_end]),
                ],
                "valid": [
                    str(index[valid_start]),
                    str(index[valid_end]),
                ],
                "test": [
                    str(index[test_start]),
                    str(index[test_end]),
                ],
            }
        )

    if len(folds) < 3:
        raise ValueError(
            "fewer than three walk-forward folds"
        )

    return folds


def median(
    values,
):
    cleaned = [
        float(value)
        for value in values
        if (
            value is not None
            and math.isfinite(
                float(value)
            )
        )
    ]

    if not cleaned:
        return None

    return float(
        np.median(cleaned)
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        required=True,
    )

    parser.add_argument(
        "--timeframe",
        default="1h",
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
        "--num-threads",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    symbols = [
        item.strip().upper()
        for item
        in args.symbols.split(",")
        if item.strip()
    ]

    horizons = [
        int(item)
        for item
        in args.hold_bars.split(",")
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

    prepared_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "swing_ml_walkforward_inputs"
    )

    prepared_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_results = []

    for symbol in symbols:
        source = (
            ROOT
            / "data"
            / "derived"
            / (
                f"{symbol}_"
                f"{args.timeframe}"
                ".parquet"
            )
        )

        if not source.is_file():
            print(
                "MISSING",
                source,
            )
            continue

        raw = load_frame(
            source
        )

        alpha_response = runner.run(
            "vnpy",
            "alpha158",
            {
                "input_parquet": (
                    str(source)
                ),
                "symbol": symbol,
                "periods": (
                    basic_periods(
                        raw.index
                    )
                ),
                "include_label": False,
                "vwap_policy": (
                    "hlc3_proxy"
                ),
                "max_workers": 1,
            },
            timeout_seconds=900,
            raise_on_error=True,
        )

        alpha_path = Path(
            alpha_response
            .artifacts[0]
            .path
        )

        alpha = load_frame(
            alpha_path
        )

        prices = (
            raw[
                [
                    "open",
                    "close",
                ]
            ]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
            .rename(
                columns={
                    "open": (
                        "_canonical_open"
                    ),
                    "close": (
                        "_canonical_close"
                    ),
                }
            )
        )

        base = alpha.join(
            prices,
            how="inner",
        )

        for hold_bars in horizons:
            frame = base.copy()

            frame["label"] = (
                forward_open_to_close_return(
                    frame[
                        "_canonical_open"
                    ],
                    frame[
                        "_canonical_close"
                    ],
                    hold_bars=hold_bars,
                )
            )

            frame["symbol"] = (
                symbol
            )

            frame = (
                frame.drop(
                    columns=[
                        "_canonical_open",
                        "_canonical_close",
                    ]
                )
                .dropna(
                    subset=[
                        "label",
                    ]
                )
            )

            dataset_path = (
                prepared_root
                / (
                    f"{symbol}_"
                    f"{args.timeframe}_"
                    f"hold{hold_bars}.parquet"
                )
            )

            frame.reset_index().to_parquet(
                dataset_path,
                index=False,
            )

            periods = rolling_periods(
                frame.index,
                hold_bars=hold_bars,
                requested_folds=(
                    args.folds
                ),
            )

            fold_results = []

            for fold_index, period in enumerate(
                periods,
                start=1,
            ):
                response = runner.run(
                    "qlib",
                    "fit_predict_lgbm",
                    {
                        "input_parquet": (
                            str(
                                dataset_path
                            )
                        ),
                        "symbol": symbol,
                        "periods": period,
                        "purge_bars": 0,
                        "label_semantics": (
                            "signal close[t]; "
                            "entry open[t+1]; "
                            f"exit close[t+{hold_bars}]"
                        ),
                        "seed": (
                            1000
                            + fold_index
                        ),
                        "num_boost_round": (
                            800
                        ),
                        "early_stopping_rounds": (
                            40
                        ),
                        "learning_rate": (
                            0.025
                        ),
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
                    symbol,
                    "HOLD",
                    hold_bars,
                    "FOLD",
                    fold_index,
                )

                print(
                    "SPEARMAN",
                    metrics.get(
                        "spearman_ic"
                    ),
                )

                print(
                    "PEARSON",
                    metrics.get(
                        "pearson_ic"
                    ),
                )

                print(
                    "BALANCED_DIRECTION",
                    metrics.get(
                        "balanced_directional_accuracy"
                    ),
                )

                print(
                    "EDGE_VS_MAJORITY",
                    metrics.get(
                        "directional_edge_vs_majority"
                    ),
                )

                print(
                    "TOP_BOTTOM_SPREAD",
                    metrics.get(
                        "top_bottom_return_spread"
                    ),
                )

            spearman_values = [
                row.get(
                    "spearman_ic"
                )
                for row in fold_results
            ]

            pearson_values = [
                row.get(
                    "pearson_ic"
                )
                for row in fold_results
            ]

            spread_values = [
                row.get(
                    "top_bottom_return_spread"
                )
                for row in fold_results
            ]

            directional_edges = [
                row.get(
                    "directional_edge_vs_majority"
                )
                for row in fold_results
            ]

            positive_spearman_ratio = float(
                np.mean(
                    [
                        (
                            value is not None
                            and float(
                                value
                            ) > 0.0
                        )
                        for value
                        in spearman_values
                    ]
                )
            )

            result = {
                "symbol": symbol,
                "timeframe": (
                    args.timeframe
                ),
                "hold_bars": (
                    hold_bars
                ),
                "fold_count": len(
                    fold_results
                ),
                "positive_spearman_ratio": (
                    positive_spearman_ratio
                ),
                "median_spearman_ic": (
                    median(
                        spearman_values
                    )
                ),
                "worst_spearman_ic": (
                    min(
                        float(v)
                        for v
                        in spearman_values
                        if v is not None
                    )
                ),
                "median_pearson_ic": (
                    median(
                        pearson_values
                    )
                ),
                "median_top_bottom_spread": (
                    median(
                        spread_values
                    )
                ),
                "median_directional_edge_vs_majority": (
                    median(
                        directional_edges
                    )
                ),
                "folds": (
                    fold_results
                ),
            }

            all_results.append(
                result
            )

            print()
            print(
                "SUMMARY",
                symbol,
                hold_bars,
            )

            print(
                "POSITIVE_SPEARMAN_RATIO",
                result[
                    "positive_spearman_ratio"
                ],
            )

            print(
                "MEDIAN_SPEARMAN",
                result[
                    "median_spearman_ic"
                ],
            )

            print(
                "WORST_SPEARMAN",
                result[
                    "worst_spearman_ic"
                ],
            )

    output = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "swing_ml_walkforward.json"
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "swing_ml_walkforward_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "results": (
                    all_results
                ),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "ARTIFACT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
