from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
)

from stocks.rl.config import (
    load_rl_yaml,
)

from stocks.rl.experiment import (
    run_walk_forward_experiment,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def parse_symbols(
    value: str,
) -> tuple[str, ...]:
    return tuple(
        part.strip().upper()
        for part in value.split(",")
        if part.strip()
    )


def load_market_frame(
    symbol: str,
    timeframe: str,
) -> tuple[pd.DataFrame, Path]:
    candidates = (
        ROOT
        / "data"
        / "derived"
        / f"{symbol}_{timeframe}.parquet",

        ROOT
        / "data"
        / "adjusted"
        / f"{symbol}_{timeframe}.parquet",

        ROOT
        / "data"
        / "processed"
        / f"{symbol}_{timeframe}.parquet",
    )

    for path in candidates:
        if path.is_file():
            frame = pd.read_parquet(
                path
            )

            return (
                canonicalize_ohlcv(
                    frame
                ),
                path,
            )

    raise FileNotFoundError(
        f"No {timeframe} dataset found "
        f"for {symbol}"
    )


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
        "--timesteps",
        type=int,
        default=10_000,
    )

    parser.add_argument(
        "--seeds",
        default="11,29,47",
    )

    parser.add_argument(
        "--max-folds",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--algorithm",
        choices=(
            "PPO",
            "SAC",
        ),
        default="PPO",
    )

    args = parser.parse_args()

    reward, environment, training, _ = (
        load_rl_yaml(
            ROOT
            / "config"
            / "rl.yaml"
        )
    )

    training = replace(
        training,
        algorithm=args.algorithm,
        total_timesteps=(
            args.timesteps
        ),
    )

    seeds = tuple(
        int(part)
        for part in args.seeds.split(",")
        if part.strip()
    )

    summaries = []

    for symbol in parse_symbols(
        args.symbols
    ):
        frame, source = (
            load_market_frame(
                symbol,
                args.timeframe,
            )
        )

        print(
            f"RL START "
            f"symbol={symbol} "
            f"timeframe={args.timeframe} "
            f"rows={len(frame)} "
            f"source={source}",
            flush=True,
        )

        result = (
            run_walk_forward_experiment(
                frame,
                symbol=symbol,
                timeframe=args.timeframe,
                output_root=(
                    ROOT
                    / "artifacts"
                    / "rl"
                    / "walk_forward"
                ),
                seeds=seeds,
                max_folds=args.max_folds,
                environment=environment,
                reward=reward,
                training=training,
            )
        )

        summary = {
            "symbol": symbol,
            "artifact": result[
                "artifact"
            ],
            **result[
                "summary"
            ],
        }

        summaries.append(
            summary
        )

        print(
            json.dumps(
                summary,
                indent=2,
            ),
            flush=True,
        )

    print(
        json.dumps(
            {
                "status": "OK",
                "execution_authority": "NONE",
                "results": summaries,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
