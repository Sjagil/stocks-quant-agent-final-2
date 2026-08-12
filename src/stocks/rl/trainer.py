from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import TrainingConfig


def train_policy(env: Any, output_path: str | Path, cfg: TrainingConfig | None = None) -> Path:
    """Train PPO or SAC through Stable-Baselines3.

    Import is local so the rest of the repository works without the optional RL stack.
    This function trains research artifacts only and has no broker connectivity.
    """
    cfg = cfg or TrainingConfig()
    try:
        from stable_baselines3 import PPO, SAC
    except Exception as exc:  # pragma: no cover
        raise ImportError("stable-baselines3 is required; install the 'rl' extra") from exc

    algo = cfg.algorithm.upper()
    if algo == "PPO":
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=cfg.learning_rate,
            n_steps=cfg.n_steps,
            batch_size=cfg.batch_size,
            gamma=cfg.gamma,
            gae_lambda=cfg.gae_lambda,
            ent_coef=cfg.ent_coef,
            clip_range=cfg.clip_range,
            seed=cfg.seed,
            verbose=1,
        )
    elif algo == "SAC":
        model = SAC(
            "MlpPolicy",
            env,
            learning_rate=cfg.learning_rate,
            batch_size=cfg.batch_size,
            gamma=cfg.gamma,
            seed=cfg.seed,
            verbose=1,
        )
    else:
        raise ValueError("algorithm must be PPO or SAC")

    model.learn(total_timesteps=cfg.total_timesteps)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(output))
    return output
