from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.integrations import (
    IntegrationRegistry,
    IntegrationRunner,
)
from stocks.research.swing_labels import (
    forward_hold_return,
    purged_periods,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def load_timestamp_frame(
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

        frame.index.name = (
            "datetime"
        )

        return frame.sort_index()

    for column in (
        "datetime",
        "timestamp",
        "timestamp_utc",
    ):
        if column in frame:
            frame = frame.copy()

            frame[column] = (
                pd.to_datetime(
                    frame[column],
                    utc=True,
                    errors="coerce",
                )
            )

            frame = (
                frame.dropna(
                    subset=[column]
                )
                .set_index(column)
                .sort_index()
            )

            frame.index.name = (
                "datetime"
            )

            return frame

    raise ValueError(
        f"{path}: no datetime"
    )


def basic_periods(
    index: pd.DatetimeIndex,
) -> dict[str, list[str]]:
    index = (
        pd.DatetimeIndex(index)
        .dropna()
        .sort_values()
        .unique()
    )

    first = int(
        len(index) * 0.60
    )

    second = int(
        len(index) * 0.80
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


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default=(
            "SPY,QQQ,AAPL,AMD,NVDA"
        ),
    )

    parser.add_argument(
        "--timeframe",
        default="1h",
    )

    parser.add_argument(
        "--hold-bars",
        default="7,21,42",
    )

    parser.add_argument(
        "--num-threads",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    symbols = [
        value.strip().upper()
        for value
        in args.symbols.split(",")
        if value.strip()
    ]

    horizons = [
        int(value)
        for value
        in args.hold_bars.split(",")
        if value.strip()
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

    result_rows = []

    prepared_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "swing_ml_inputs"
    )

    prepared_root.mkdir(
        parents=True,
        exist_ok=True,
    )

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
                symbol,
                source,
            )

            continue

        raw = load_timestamp_frame(
            source
        )

        alpha_response = (
            runner.run(
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
        )

        alpha_path = Path(
            alpha_response.artifacts[
                0
            ].path
        )

        alpha = (
            load_timestamp_frame(
                alpha_path
            )
        )

        close = pd.to_numeric(
            raw["close"],
            errors="coerce",
        ).rename(
            "_canonical_close"
        )

        base = alpha.join(
            close,
            how="inner",
        )

        for hold_bars in horizons:
            frame = base.copy()

            frame["label"] = (
                forward_hold_return(
                    frame[
                        "_canonical_close"
                    ],
                    hold_bars=hold_bars,
                )
            )

            frame["symbol"] = (
                symbol
            )

            frame = frame.drop(
                columns=[
                    "_canonical_close",
                ],
            )

            frame = frame.dropna(
                subset=[
                    "label",
                ]
            )

            periods = (
                purged_periods(
                    frame.index,
                    lookahead_bars=(
                        hold_bars + 1
                    ),
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

            semantics = (
                f"next-bar entry; "
                f"hold {hold_bars} bars; "
                f"close[t+{hold_bars + 1}]"
                f"/close[t+1]-1"
            )

            response = runner.run(
                "qlib",
                "fit_predict_lgbm",
                {
                    "input_parquet": (
                        str(dataset_path)
                    ),
                    "symbol": symbol,
                    "periods": periods,
                    "purge_bars": 0,
                    "label_semantics": (
                        semantics
                    ),
                    "seed": 42,
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

            result_rows.append(
                {
                    "symbol": symbol,
                    "timeframe": (
                        args.timeframe
                    ),
                    "hold_bars": (
                        hold_bars
                    ),
                    **metrics,
                }
            )

            print()
            print(
                symbol,
                "HOLD",
                hold_bars,
            )

            print(
                "DIRECTION",
                metrics.get(
                    "directional_accuracy"
                ),
            )

            print(
                "PEARSON",
                metrics.get(
                    "pearson_ic"
                ),
            )

            print(
                "SPEARMAN",
                metrics.get(
                    "spearman_ic"
                ),
            )

    artifact = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "swing_ml_horizons.json"
    )

    artifact.write_text(
        json.dumps(
            {
                "schema": (
                    "swing_ml_horizons_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "results": (
                    result_rows
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
        artifact,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
