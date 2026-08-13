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
from stocks.research.walkforward_splits import rolling_periods


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


VARIANTS = {
    "BASE": (),
    "TACTICAL": (
        "15m",
    ),
    "SWING_ONLY": (
        "2h",
        "4h",
    ),
    "STRUCTURE_ONLY": (
        "1d",
        "1w",
    ),
    "FULL": (
        "15m",
        "2h",
        "4h",
        "1d",
        "1w",
    ),
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

        frame[column] = (
            pd.to_datetime(
                frame[column],
                utc=True,
                errors="coerce",
            )
        )

        return (
            frame.dropna(
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

    for path in candidates:
        if path.is_file():
            return path

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

    result = []

    for column in frame.columns:
        if column in excluded:
            continue

        numeric = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

        if numeric.notna().any():
            result.append(
                column
            )

    return result


def context_columns(
    frame: pd.DataFrame,
    timeframes: tuple[str, ...],
) -> list[str]:
    result = []

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
                frame[column],
                errors="coerce",
            )

            if numeric.notna().any():
                result.append(
                    column
                )

    return list(
        dict.fromkeys(
            result
        )
    )


def finite_values(
    rows: list[dict],
    key: str,
) -> list[float]:
    values = []

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
            values.append(
                value
            )

    return values


def summarize(
    folds: list[dict],
) -> dict:
    spearman = finite_values(
        folds,
        "spearman_ic",
    )

    pearson = finite_values(
        folds,
        "pearson_ic",
    )

    spread = finite_values(
        folds,
        "top_bottom_return_spread",
    )

    direction = finite_values(
        folds,
        "directional_edge_vs_majority",
    )

    return {
        "fold_count": len(
            folds
        ),
        "positive_spearman_ratio": (
            float(
                np.mean(
                    [
                        value > 0
                        for value
                        in spearman
                    ]
                )
            )
            if spearman
            else None
        ),
        "median_spearman_ic": (
            float(
                np.median(
                    spearman
                )
            )
            if spearman
            else None
        ),
        "worst_spearman_ic": (
            float(
                min(
                    spearman
                )
            )
            if spearman
            else None
        ),
        "median_pearson_ic": (
            float(
                np.median(
                    pearson
                )
            )
            if pearson
            else None
        ),
        "median_top_bottom_spread": (
            float(
                np.median(
                    spread
                )
            )
            if spread
            else None
        ),
        "median_directional_edge_vs_majority": (
            float(
                np.median(
                    direction
                )
            )
            if direction
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cases",
        required=True,
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

    cases = []

    for item in args.cases.split(
        ","
    ):
        symbol, hold = (
            item.strip()
            .upper()
            .split(
                ":",
                1,
            )
        )

        cases.append(
            (
                symbol,
                int(
                    hold
                ),
            )
        )

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
        / "mtf_qlib_ablation_inputs"
    )

    prepared_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_results = []

    for symbol, hold_bars in cases:
        source = one_hour_source(
            symbol
        )

        raw = load_frame(
            source
        )

        alpha_response = runner.run(
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
                            raw.index[0]
                        ),
                        str(
                            raw.index[
                                int(
                                    len(
                                        raw
                                    )
                                    * 0.60
                                )
                            ]
                        ),
                    ],
                    "valid": [
                        str(
                            raw.index[
                                int(
                                    len(
                                        raw
                                    )
                                    * 0.60
                                )
                                + 1
                            ]
                        ),
                        str(
                            raw.index[
                                int(
                                    len(
                                        raw
                                    )
                                    * 0.80
                                )
                            ]
                        ),
                    ],
                    "test": [
                        str(
                            raw.index[
                                int(
                                    len(
                                        raw
                                    )
                                    * 0.80
                                )
                                + 1
                            ]
                        ),
                        str(
                            raw.index[-1]
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

        alpha = load_frame(
            Path(
                alpha_response
                .artifacts[0]
                .path
            )
        )

        alpha_features = (
            alpha_columns(
                alpha
            )
        )

        label = (
            forward_open_to_close_return(
                pd.to_numeric(
                    raw["open"],
                    errors="coerce",
                ),
                pd.to_numeric(
                    raw["close"],
                    errors="coerce",
                ),
                hold_bars=hold_bars,
            )
            .rename(
                "label"
            )
        )

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

        tactical_available = (
            mtf.loc[
                mtf[
                    "15m_available"
                ]
                == 1,
                "decision_bar_time",
            ]
        )

        if tactical_available.empty:
            raise ValueError(
                f"{symbol}: no causal "
                "15m common sample"
            )

        common_start = (
            tactical_available.min()
        )

        all_context_columns = (
            context_columns(
                mtf,
                VARIANTS[
                    "FULL"
                ],
            )
        )

        mtf_by_bar = (
            mtf[
                [
                    "decision_time",
                    *all_context_columns,
                ]
            ]
            .copy()
        )

        mtf_by_bar.index = (
            mtf[
                "decision_bar_time"
            ]
        )

        mtf_by_bar.index.name = (
            "datetime"
        )

        combined = (
            alpha[
                alpha_features
            ]
            .join(
                label,
                how="inner",
            )
            .join(
                mtf_by_bar,
                how="inner",
            )
        )

        combined = combined.loc[
            combined.index
            >= common_start
        ].copy()

        combined = combined.dropna(
            subset=[
                "label",
                "decision_time",
            ]
        )

        combined = combined.sort_values(
            "decision_time"
        )

        if (
            combined[
                "decision_time"
            ]
            .duplicated()
            .any()
        ):
            raise ValueError(
                f"{symbol}: duplicate "
                "decision times"
            )

        periods = rolling_periods(
            pd.DatetimeIndex(
                combined[
                    "decision_time"
                ]
            ),
            hold_bars=hold_bars,
            requested_folds=(
                args.folds
            ),
        )

        case_results = []

        for variant, timeframes in (
            VARIANTS.items()
        ):
            context_features = (
                context_columns(
                    mtf,
                    timeframes,
                )
            )

            features = [
                *alpha_features,
                *context_features,
            ]

            dataset = combined[
                [
                    "decision_time",
                    *features,
                    "label",
                ]
            ].copy()

            dataset = dataset.rename(
                columns={
                    "decision_time": (
                        "datetime"
                    ),
                }
            )

            dataset[
                "symbol"
            ] = symbol

            dataset_path = (
                prepared_root
                / (
                    f"{symbol}_"
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
                        "preserve_feature_missingness": (
                            True
                        ),
                        "label_semantics": (
                            "signal close[t]; "
                            "entry open[t+1]; "
                            f"exit close[t+{hold_bars}]"
                        ),
                        "seed": (
                            1000
                            + fold_index
                        ),
                        "num_boost_round": 800,
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
                    hold_bars,
                    variant,
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
                    "SPREAD",
                    metrics.get(
                        "top_bottom_return_spread"
                    ),
                )
                print(
                    "MISSING",
                    metrics.get(
                        "feature_missing_fraction"
                    ),
                )

            summary = summarize(
                fold_results
            )

            case_results.append(
                {
                    "variant": variant,
                    "timeframes": list(
                        timeframes
                    ),
                    "feature_count": len(
                        features
                    ),
                    "common_rows": len(
                        combined
                    ),
                    "common_start": str(
                        common_start
                    ),
                    **summary,
                    "folds": (
                        fold_results
                    ),
                }
            )

        baseline = next(
            row
            for row in case_results
            if row[
                "variant"
            ]
            == "BASE"
        )

        base_ic = baseline[
            "median_spearman_ic"
        ]

        base_worst = baseline[
            "worst_spearman_ic"
        ]

        for row in case_results:
            row[
                "delta_median_spearman_vs_base"
            ] = (
                row[
                    "median_spearman_ic"
                ]
                - base_ic
                if (
                    row[
                        "median_spearman_ic"
                    ]
                    is not None
                    and base_ic
                    is not None
                )
                else None
            )

            row[
                "delta_worst_spearman_vs_base"
            ] = (
                row[
                    "worst_spearman_ic"
                ]
                - base_worst
                if (
                    row[
                        "worst_spearman_ic"
                    ]
                    is not None
                    and base_worst
                    is not None
                )
                else None
            )

        all_results.append(
            {
                "symbol": symbol,
                "hold_bars": hold_bars,
                "one_hour_source": str(
                    source
                ),
                "common_rows": len(
                    combined
                ),
                "common_start": str(
                    common_start
                ),
                "fold_count": len(
                    periods
                ),
                "variants": (
                    case_results
                ),
            }
        )

        print()
        print(
            "=" * 70
        )
        print(
            "SUMMARY",
            symbol,
            hold_bars,
        )

        for row in case_results:
            print(
                row[
                    "variant"
                ],
                "MEDIAN_IC=",
                row[
                    "median_spearman_ic"
                ],
                "WORST=",
                row[
                    "worst_spearman_ic"
                ],
                "DELTA=",
                row[
                    "delta_median_spearman_vs_base"
                ],
            )

    output = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "mtf_qlib_ablation.json"
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "mtf_qlib_ablation_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
                "variants": {
                    key: list(
                        value
                    )
                    for key, value
                    in VARIANTS.items()
                },
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
    raise SystemExit(
        main()
    )
