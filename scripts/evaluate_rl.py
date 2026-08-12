from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stocks.rl import LongOnlySwingEnv, build_rl_features, load_rl_yaml
from stocks.rl.evaluator import evaluate_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parquet", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/rl.yaml"))
    parser.add_argument("--algorithm", choices=["PPO", "SAC"], default="PPO")
    args = parser.parse_args()

    from stable_baselines3 import PPO, SAC

    reward_cfg, env_cfg, _, _ = load_rl_yaml(args.config)
    frame = pd.read_parquet(args.parquet).sort_index()
    env = LongOnlySwingEnv(build_rl_features(frame), frame["close"], env_cfg=env_cfg, reward_cfg=reward_cfg)
    cls = PPO if args.algorithm == "PPO" else SAC
    model = cls.load(str(args.model), env=env)
    print(evaluate_policy(model, env))


if __name__ == "__main__":
    main()
