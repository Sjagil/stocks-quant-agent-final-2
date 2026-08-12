from __future__ import annotations

import argparse
from pathlib import Path
from dataclasses import replace

import pandas as pd

from stocks.rl import LongOnlySwingEnv, build_rl_features, load_rl_yaml
from stocks.rl.trainer import train_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parquet", type=Path, help="Closed-candle OHLCV parquet")
    parser.add_argument("--config", type=Path, default=Path("config/rl.yaml"))
    parser.add_argument("--model-out", type=Path, default=Path("artifacts/models/ppo_swing"))
    parser.add_argument("--timesteps", type=int, default=None)
    parser.add_argument("--algorithm", choices=["PPO", "SAC"], default=None)
    parser.add_argument("--n-steps", type=int, default=None, help="PPO rollout length; ignored by SAC")
    args = parser.parse_args()

    reward_cfg, env_cfg, train_cfg, _ = load_rl_yaml(args.config)
    train_cfg = replace(
        train_cfg,
        algorithm=args.algorithm or train_cfg.algorithm,
        total_timesteps=args.timesteps if args.timesteps is not None else train_cfg.total_timesteps,
        n_steps=args.n_steps if args.n_steps is not None else train_cfg.n_steps,
    )
    frame = pd.read_parquet(args.parquet).sort_index()
    features = build_rl_features(frame)
    env = LongOnlySwingEnv(features, frame["close"], env_cfg=env_cfg, reward_cfg=reward_cfg)
    output = train_policy(env, args.model_out, train_cfg)
    print(f"saved_model={output}.zip")


if __name__ == "__main__":
    main()
