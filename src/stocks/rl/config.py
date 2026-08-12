from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RewardConfig:
    transaction_cost_bps: float = 5.0
    slippage_bps: float = 3.0
    turnover_penalty: float = 0.10
    downside_penalty: float = 0.20
    drawdown_penalty: float = 0.30
    inactivity_penalty: float = 0.0
    reward_clip: float = 5.0

    @property
    def round_trip_cost_rate(self) -> float:
        return 2.0 * (self.transaction_cost_bps + self.slippage_bps) / 10_000.0


@dataclass(frozen=True)
class EnvironmentConfig:
    window_size: int = 64
    max_position: float = 1.0
    min_trade_delta: float = 0.01
    initial_equity: float = 10_000.0


@dataclass(frozen=True)
class TrainingConfig:
    algorithm: str = "PPO"
    total_timesteps: int = 250_000
    seed: int = 42
    learning_rate: float = 3e-5
    n_steps: int = 2048
    batch_size: int = 256
    gamma: float = 0.995
    gae_lambda: float = 0.95
    ent_coef: float = 0.005
    clip_range: float = 0.10


def load_rl_yaml(path: str | Path = "config/rl.yaml") -> tuple[RewardConfig, EnvironmentConfig, TrainingConfig, dict]:
    """Load the repository RL YAML. PyYAML is required only for RL runtime commands."""
    try:
        import yaml
    except Exception as exc:
        raise ImportError("pyyaml is required to load RL config; install the 'rl' extra") from exc

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("RL config root must be a mapping")
    reward = RewardConfig(**(payload.get("reward") or {}))
    environment = EnvironmentConfig(**(payload.get("environment") or {}))
    training = TrainingConfig(**(payload.get("training") or {}))
    promotion = dict(payload.get("promotion") or {})
    if str(promotion.get("execution_authority", "NONE")).upper() != "NONE":
        raise ValueError("RL promotion config may not grant execution authority")
    return reward, environment, training, promotion
