from __future__ import annotations

import gc
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from stocks.rl.config import EnvironmentConfig, RewardConfig

from .environments import (
    ContinuousLongOnlySizingEnv,
    DiscreteLongOnlyTimingEnv,
    RiskReductionEnv,
)


def _write_manifest(
    directory: Path,
    payload: dict[str, Any],
) -> Path:
    path = directory / "manifest.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def _status(training_mode: str) -> str:
    mode = str(training_mode).upper()
    if mode == "SMOKE":
        return "SMOKE_ONLY"
    if mode in {"VALIDATION_FOLD", "FULL"}:
        return "TRAINED_UNVALIDATED"
    if mode == "DEPLOYMENT":
        return "SHADOW_VALIDATED"
    raise ValueError(f"unsupported training_mode: {training_mode}")


def train_dqn(
    frame,
    *,
    output_dir: str | Path,
    timesteps: int,
    seed: int,
    env_cfg: EnvironmentConfig | None = None,
    reward_cfg: RewardConfig | None = None,
    training_mode: str = "FULL",
    episode_length: int | None = 256,
) -> dict[str, Any]:
    from stable_baselines3 import DQN

    env_cfg = env_cfg or EnvironmentConfig(window_size=32)
    reward_cfg = reward_cfg or RewardConfig()
    env = DiscreteLongOnlyTimingEnv(
        frame,
        env_cfg=env_cfg,
        reward_cfg=reward_cfg,
        random_start=True,
        episode_length=episode_length,
    )
    model = DQN(
        "MlpPolicy",
        env,
        learning_rate=1e-4,
        buffer_size=40_000,
        learning_starts=min(500, max(100, int(timesteps) // 10)),
        batch_size=128,
        gamma=0.995,
        train_freq=4,
        gradient_steps=1,
        target_update_interval=500,
        exploration_fraction=0.20,
        exploration_final_eps=0.03,
        policy_kwargs={"net_arch": [128, 128]},
        seed=int(seed),
        verbose=1,
    )
    model.learn(total_timesteps=int(timesteps))

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model"
    model.save(str(model_path))

    manifest = {
        "schema": "agent_model_v2_14",
        "algorithm": "DQN",
        "role": "ENTRY_EXIT_TIMING",
        "seed": int(seed),
        "timesteps": int(timesteps),
        "training_mode": str(training_mode).upper(),
        "research_status": _status(training_mode),
        "environment": asdict(env_cfg),
        "reward": asdict(reward_cfg),
        "action_semantics": ["HOLD", "ENTER_LONG", "EXIT_TO_CASH"],
        "can_short": False,
        "money_control": False,
        "execution_authority": "NONE",
        "model_path": str(model_path) + ".zip",
    }
    manifest_path = _write_manifest(directory, manifest)
    manifest["manifest"] = str(manifest_path)
    try:
        env.close()
    except Exception:
        pass
    del model
    gc.collect()
    return manifest


def train_sac(
    frame,
    *,
    output_dir: str | Path,
    timesteps: int,
    seed: int,
    env_cfg: EnvironmentConfig | None = None,
    reward_cfg: RewardConfig | None = None,
    training_mode: str = "FULL",
    episode_length: int | None = 256,
) -> dict[str, Any]:
    from stable_baselines3 import SAC

    env_cfg = env_cfg or EnvironmentConfig(window_size=32)
    reward_cfg = reward_cfg or RewardConfig()
    env = ContinuousLongOnlySizingEnv(
        frame,
        env_cfg=env_cfg,
        reward_cfg=reward_cfg,
        random_start=True,
        episode_length=episode_length,
    )

    model = SAC(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        buffer_size=50_000,
        learning_starts=min(1000, max(100, int(timesteps) // 10)),
        batch_size=256,
        tau=0.005,
        gamma=0.995,
        train_freq=1,
        gradient_steps=1,
        ent_coef="auto",
        policy_kwargs={"net_arch": [128, 128]},
        seed=int(seed),
        verbose=1,
    )
    model.learn(total_timesteps=int(timesteps))

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model"
    model.save(str(model_path))

    manifest = {
        "schema": "agent_model_v2_14",
        "algorithm": "SAC",
        "role": "CONTINUOUS_TARGET_EXPOSURE",
        "seed": int(seed),
        "timesteps": int(timesteps),
        "training_mode": str(training_mode).upper(),
        "research_status": _status(training_mode),
        "environment": asdict(env_cfg),
        "reward": asdict(reward_cfg),
        "target_exposure_range": [0.0, float(env_cfg.max_position)],
        "can_short": False,
        "money_control": False,
        "execution_authority": "NONE",
        "model_path": str(model_path) + ".zip",
    }
    manifest_path = _write_manifest(directory, manifest)
    manifest["manifest"] = str(manifest_path)
    try:
        env.close()
    except Exception:
        pass
    del model
    gc.collect()
    return manifest


def train_maskable_ppo_risk(
    frame,
    *,
    output_dir: str | Path,
    timesteps: int,
    seed: int,
    env_cfg: EnvironmentConfig | None = None,
    reward_cfg: RewardConfig | None = None,
    training_mode: str = "FULL",
    episode_length: int | None = 256,
) -> dict[str, Any]:
    from sb3_contrib import MaskablePPO

    env_cfg = env_cfg or EnvironmentConfig(window_size=24)
    reward_cfg = reward_cfg or RewardConfig()
    env = RiskReductionEnv(
        frame,
        env_cfg=env_cfg,
        reward_cfg=reward_cfg,
        random_start=True,
        episode_length=episode_length,
    )

    n_steps = min(512, max(64, int(timesteps) // 4))
    batch_size = min(128, n_steps)

    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=n_steps,
        batch_size=batch_size,
        gamma=0.995,
        gae_lambda=0.95,
        ent_coef=0.005,
        clip_range=0.10,
        seed=int(seed),
        verbose=0,
    )
    model.learn(total_timesteps=int(timesteps))

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model"
    model.save(str(model_path))

    manifest = {
        "schema": "agent_model_v2_14",
        "algorithm": "MASKABLE_PPO",
        "role": "POSITION_RISK_REDUCTION",
        "seed": int(seed),
        "timesteps": int(timesteps),
        "training_mode": str(training_mode).upper(),
        "research_status": _status(training_mode),
        "environment": asdict(env_cfg),
        "reward": asdict(reward_cfg),
        "actions": ["KEEP", "CUT_25", "CUT_50", "FLAT"],
        "can_open": False,
        "can_increase_position": False,
        "can_short": False,
        "money_control": False,
        "execution_authority": "NONE",
        "model_path": str(model_path) + ".zip",
    }
    manifest_path = _write_manifest(directory, manifest)
    manifest["manifest"] = str(manifest_path)
    try:
        env.close()
    except Exception:
        pass
    del model
    gc.collect()
    return manifest


def train_agent(
    algorithm: str,
    frame,
    *,
    output_dir: str | Path,
    timesteps: int,
    seed: int,
    reward_cfg: RewardConfig | None = None,
    training_mode: str = "FULL",
    episode_length: int | None = 256,
) -> dict[str, Any]:
    algorithm = algorithm.upper()
    kwargs = dict(
        output_dir=output_dir,
        timesteps=int(timesteps),
        seed=int(seed),
        reward_cfg=reward_cfg,
        training_mode=training_mode,
        episode_length=episode_length,
    )
    if algorithm == "DQN":
        return train_dqn(frame, **kwargs)
    if algorithm == "SAC":
        return train_sac(frame, **kwargs)
    if algorithm == "MASKABLE_PPO":
        return train_maskable_ppo_risk(frame, **kwargs)
    raise ValueError(f"unsupported algorithm: {algorithm}")


def load_agent_model(
    algorithm: str,
    model_path: str | Path,
):
    algorithm = algorithm.upper()
    if algorithm == "DQN":
        from stable_baselines3 import DQN
        return DQN.load(str(model_path))
    if algorithm == "SAC":
        from stable_baselines3 import SAC
        return SAC.load(str(model_path))
    if algorithm == "MASKABLE_PPO":
        from sb3_contrib import MaskablePPO
        return MaskablePPO.load(str(model_path))
    raise ValueError(f"unsupported algorithm: {algorithm}")
