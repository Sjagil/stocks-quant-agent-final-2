from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.integrations import (
    IntegrationRegistry,
    IntegrationRunner,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def datetime_index(
    path: Path,
) -> pd.DatetimeIndex:
    frame = pd.read_parquet(
        path
    )

    if isinstance(
        frame.index,
        pd.DatetimeIndex,
    ):
        index = frame.index

    else:
        candidate = None

        for column in (
            "timestamp",
            "datetime",
            "timestamp_utc",
        ):
            if column in frame:
                candidate = column
                break

        if candidate is None:
            raise ValueError(
                f"{path}: no timestamp"
            )

        index = pd.to_datetime(
            frame[
                candidate
            ],
            utc=True,
        )

    index = pd.DatetimeIndex(
        index
    )

    if index.tz is None:
        index = index.tz_localize(
            "UTC"
        )
    else:
        index = index.tz_convert(
            "UTC"
        )

    return index.sort_values()


def periods_for(
    index: pd.DatetimeIndex,
) -> dict:
    if len(index) < 500:
        raise ValueError(
            "at least 500 rows required"
        )

    train_boundary = int(
        len(index)
        * 0.60
    )

    valid_boundary = int(
        len(index)
        * 0.80
    )

    return {
        "train": [
            str(
                index[
                    0
                ]
            ),
            str(
                index[
                    train_boundary
                    - 1
                ]
            ),
        ],
        "valid": [
            str(
                index[
                    train_boundary
                ]
            ),
            str(
                index[
                    valid_boundary
                    - 1
                ]
            ),
        ],
        "test": [
            str(
                index[
                    valid_boundary
                ]
            ),
            str(
                index[
                    -1
                ]
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default="SPY",
    )

    parser.add_argument(
        "--timeframe",
        default="1h",
    )

    parser.add_argument(
        "--purge-bars",
        type=int,
        default=3,
    )

    args = parser.parse_args()

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

    all_results = []

    for symbol in (
        value.strip().upper()
        for value
        in args.symbols.split(",")
        if value.strip()
    ):
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
                symbol,
                "MISSING",
                source,
            )

            continue

        index = datetime_index(
            source
        )

        periods = periods_for(
            index
        )

        print()
        print(
            "ALPHA158 START",
            symbol,
        )

        vnpy = runner.run(
            "vnpy",
            "alpha158",
            {
                "input_parquet": (
                    str(
                        source
                    )
                ),
                "symbol": symbol,
                "periods": periods,
                "include_label": True,
                "vwap_policy": (
                    "hlc3_proxy"
                ),
                "max_workers": 1,
            },
            timeout_seconds=900,
            raise_on_error=True,
        )

        if not vnpy.artifacts:
            raise RuntimeError(
                "VNpy returned no artifact"
            )

        alpha_path = Path(
            vnpy.artifacts[
                0
            ].path
        )

        print(
            "ALPHA158 OK",
            alpha_path,
        )

        print(
            "QLIB START",
            symbol,
        )

        qlib = runner.run(
            "qlib",
            "fit_predict_lgbm",
            {
                "input_parquet": (
                    str(
                        alpha_path
                    )
                ),
                "symbol": symbol,
                "periods": periods,
                "purge_bars": (
                    args.purge_bars
                ),
                "seed": 42,
                "num_boost_round": 500,
                "early_stopping_rounds": 30,
                "learning_rate": 0.03,
                "num_leaves": 31,
                "num_threads": 4,
            },
            timeout_seconds=900,
            raise_on_error=True,
        )

        print(
            "QLIB OK"
        )

        print(
            json.dumps(
                qlib.data,
                indent=2,
                default=str,
            )
        )

        all_results.append(
            {
                "symbol": symbol,
                "alpha158": (
                    vnpy.to_dict()
                ),
                "qlib": (
                    qlib.to_dict()
                ),
            }
        )

    output = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "alpha_ml_chain.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "alpha_ml_chain_v1"
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
        "CHAIN ARTIFACT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
