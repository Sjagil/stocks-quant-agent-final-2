from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from stocks.rl.config import load_rl_yaml
from stocks.rl.evaluator import evaluate_policy
from stocks.rl.trainer import load_policy

from .contracts_v2_40 import AgentSpecV240, TrainingResultV240
from .dataset_v2_40 import build_windows_v240, load_dataset_v240, make_env_v240
from .sb3_continuous_trainer_v2_40 import train_or_continue_sb3_v240


def train_agent_v240(project_root: str | Path, spec: AgentSpecV240, config: dict) -> TrainingResultV240:
    root = Path(project_root).resolve()
    learning = config.get("learning") or {}
    paths = config.get("paths") or {}
    data_path = Path(spec.data_path)
    if not data_path.is_absolute():
        data_path = root / data_path
    if not data_path.is_file():
        raise FileNotFoundError(data_path)

    features, close = load_dataset_v240(data_path)
    windows = build_windows_v240(
        features,
        close,
        validation_fraction=float(learning.get("validation_fraction", 0.15)),
        test_fraction=float(learning.get("test_fraction", 0.15)),
        purge_bars=int(learning.get("purge_bars", 64)),
        minimum_rows=int(learning.get("minimum_rows", 800)),
    )
    reward_cfg, env_cfg, base_train_cfg, _ = load_rl_yaml(root / "config/rl.yaml")
    train_env = make_env_v240(windows, "train", env_cfg=env_cfg, reward_cfg=reward_cfg)

    models_root = Path(paths["models"])
    if not models_root.is_absolute():
        models_root = root / models_root
    model_base = models_root / spec.agent_id / "current"
    replay = models_root / spec.agent_id / "replay_buffer.pkl" if spec.algorithm.upper() == "SAC" else None
    model_kwargs = {}
    if spec.algorithm.upper() == "PPO":
        model_kwargs = {
            "learning_rate": base_train_cfg.learning_rate,
            "n_steps": base_train_cfg.n_steps,
            "batch_size": base_train_cfg.batch_size,
            "gamma": base_train_cfg.gamma,
            "gae_lambda": base_train_cfg.gae_lambda,
            "ent_coef": base_train_cfg.ent_coef,
            "clip_range": base_train_cfg.clip_range,
        }
    else:
        model_kwargs = {
            "learning_rate": base_train_cfg.learning_rate,
            "buffer_size": base_train_cfg.sac_buffer_size,
            "learning_starts": base_train_cfg.sac_learning_starts,
            "batch_size": base_train_cfg.batch_size,
            "tau": base_train_cfg.sac_tau,
            "gamma": base_train_cfg.gamma,
            "train_freq": base_train_cfg.sac_train_freq,
            "gradient_steps": base_train_cfg.sac_gradient_steps,
            "ent_coef": base_train_cfg.sac_ent_coef,
        }
    trained = train_or_continue_sb3_v240(
        algorithm=spec.algorithm,
        env=train_env,
        model_base=model_base,
        total_timesteps=spec.timesteps_per_update,
        seed=spec.seed,
        warm_start=bool(learning.get("warm_start", True)),
        replay_buffer_path=replay,
        model_kwargs=model_kwargs,
    )

    val_env = make_env_v240(windows, "validation", env_cfg=env_cfg, reward_cfg=reward_cfg)
    val_model = load_policy(trained["model_path"], algorithm=spec.algorithm, env=val_env)
    validation = asdict(evaluate_policy(val_model, val_env))
    test_env = make_env_v240(windows, "test", env_cfg=env_cfg, reward_cfg=reward_cfg)
    test_model = load_policy(trained["model_path"], algorithm=spec.algorithm, env=test_env)
    test = asdict(evaluate_policy(test_model, test_env))

    return TrainingResultV240(
        agent_id=spec.agent_id,
        algorithm=spec.algorithm.upper(),
        status="SUCCEEDED",
        warm_started=bool(trained["warm_started"]),
        timesteps=int(trained["timesteps"]),
        model_path=trained["model_path"],
        replay_buffer_path=trained.get("replay_buffer_path"),
        validation=validation,
        test=test,
        data_rows=windows.rows,
        train_rows=windows.train_slice[1] - windows.train_slice[0],
        validation_rows=windows.validation_slice[1] - windows.validation_slice[0],
        test_rows=windows.test_slice[1] - windows.test_slice[0],
        latest_data_time=windows.latest_data_time,
    )


__all__ = ["train_agent_v240"]
