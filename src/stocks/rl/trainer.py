from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import TrainingConfig


def _algorithm_class(
    algorithm: str,
):
    try:
        from stable_baselines3 import PPO, SAC
    except Exception as exc:
        raise ImportError(
            "stable-baselines3 is required"
        ) from exc

    name = algorithm.upper()

    if name == "PPO":
        return PPO

    if name == "SAC":
        return SAC

    raise ValueError(
        "algorithm must be PPO or SAC"
    )


def train_policy(
    env: Any,
    output_path: str | Path,
    cfg: TrainingConfig | None = None,
    *,
    verbose: int = 0,
) -> Path:
    cfg = cfg or TrainingConfig()

    cls = _algorithm_class(
        cfg.algorithm
    )

    if cfg.algorithm.upper() == "PPO":
        model = cls(
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
            verbose=verbose,
        )

    else:
        model = cls(
            "MlpPolicy",
            env,
            learning_rate=cfg.learning_rate,
            batch_size=cfg.batch_size,
            gamma=cfg.gamma,
            seed=cfg.seed,
            verbose=verbose,
        )

    model.learn(
        total_timesteps=cfg.total_timesteps
    )

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save(
        str(output)
    )

    return output


def load_policy(
    path: str | Path,
    *,
    algorithm: str,
    env: Any | None = None,
):
    cls = _algorithm_class(
        algorithm
    )

    return cls.load(
        str(path),
        env=env,
    )
