#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from stocks.agents.candle_fabric import frame_for_timeframe
from stocks.agents.trainers import (
    train_dqn,
    train_maskable_ppo_risk,
    train_sac,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="AAPL")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--algorithms",
        default="DQN,SAC,MASKABLE_PPO",
    )
    args = parser.parse_args()

    config = yaml.safe_load(
        (ROOT / "config/agent_fabric_v2_12.yaml").read_text(
            encoding="utf-8"
        )
    )
    training = config["training"]
    timesteps_map = (
        training["smoke_timesteps"]
        if args.smoke
        else training["full_timesteps"]
    )

    algorithms = {
        item.strip().upper()
        for item in args.algorithms.split(",")
        if item.strip()
    }
    symbols = [
        item.strip().upper()
        for item in args.symbols.split(",")
        if item.strip()
    ]

    results = []

    for symbol in symbols:
        frame = frame_for_timeframe(
            ROOT,
            symbol,
            args.timeframe,
        )

        for algorithm in (
            "DQN",
            "SAC",
            "MASKABLE_PPO",
        ):
            if algorithm not in algorithms:
                continue

            output_dir = (
                ROOT
                / "artifacts/agent_models/v2_12"
                / symbol
                / args.timeframe
                / algorithm
                / f"seed_{int(args.seed)}"
            )
            timesteps = int(
                timesteps_map[algorithm]
            )

            print(
                "TRAIN",
                symbol,
                args.timeframe,
                algorithm,
                "TIMESTEPS",
                timesteps,
                "SEED",
                args.seed,
            )

            common = dict(
                output_dir=output_dir,
                timesteps=timesteps,
                seed=args.seed,
                training_mode=(
                    "SMOKE"
                    if args.smoke
                    else "FULL"
                ),
                episode_length=256,
            )

            if algorithm == "DQN":
                result = train_dqn(
                    frame,
                    **common,
                )
            elif algorithm == "SAC":
                result = train_sac(
                    frame,
                    **common,
                )
            else:
                result = train_maskable_ppo_risk(
                    frame,
                    **common,
                )

            result["symbol"] = symbol
            result["timeframe"] = args.timeframe
            results.append(result)

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_training_v2_12"
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "last_run.json").write_text(
        json.dumps(
            {
                "schema": "agent_training_v2_13_compatible",
                "smoke": bool(args.smoke),
                "models": results,
                "money_control": False,
                "execution_authority": "NONE",
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "AGENT_TRAINING_V2_12 COMPLETE MODE",
        "SMOKE" if args.smoke else "FULL",
    )
    print("MODELS", len(results))
    print("SMOKE_MODELS_HAVE_DECISION_AUTHORITY False")
    print("MONEY_CONTROL False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
