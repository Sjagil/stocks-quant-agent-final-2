from __future__ import annotations

"""Reference entrypoint for shadow inference.

Wire this into the existing repository scheduler/supervisor. It intentionally does
not contain an infinite loop or IBKR order path. Scheduling and broker authority
remain owned by the main repository.
"""

import argparse
from pathlib import Path

import pandas as pd

from stocks.rl import LongOnlySwingEnv, build_rl_features, load_rl_yaml
from stocks.rl.shadow_policy import infer_shadow


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("parquet", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/rl.yaml"))
    parser.add_argument("--algorithm", choices=["PPO", "SAC"], default="PPO")
    args = parser.parse_args()

    from stable_baselines3 import PPO, SAC

    reward_cfg, env_cfg, _, _ = load_rl_yaml(args.config)
    frame = pd.read_parquet(args.parquet).sort_index()
    env = LongOnlySwingEnv(build_rl_features(frame), frame["close"], env_cfg=env_cfg, reward_cfg=reward_cfg)
    model_cls = PPO if args.algorithm == "PPO" else SAC
    model = model_cls.load(str(args.model), env=env)
    obs, _ = env.reset()
    suggestion = infer_shadow(model, obs, symbol=args.symbol, model_id=args.model.name)
    print(suggestion)


if __name__ == "__main__":
    main()
