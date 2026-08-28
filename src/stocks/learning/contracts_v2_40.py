from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class AgentStateV240(str, Enum):
    IDLE = "IDLE"
    TRAINING = "TRAINING"
    READY = "READY"
    WAITING_DATA = "WAITING_DATA"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class AgentSpecV240:
    agent_id: str
    algorithm: str
    symbol: str
    timeframe: str
    data_path: str
    enabled: bool = True
    timesteps_per_update: int = 50_000
    seed: int = 42
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.execution_authority != "NONE":
            raise ValueError("learning agents may not hold execution authority")
        if self.algorithm.upper() not in {"PPO", "SAC"}:
            raise ValueError("agent algorithm must be PPO or SAC")
        if self.timesteps_per_update <= 0:
            raise ValueError("timesteps_per_update must be positive")

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RetrainDecisionV240:
    should_train: bool
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    new_rows: int
    shadow_outcomes: int
    drift_severity: float
    model_age_hours: float | None
    execution_authority: str = "NONE"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrainingResultV240:
    agent_id: str
    algorithm: str
    status: str
    warm_started: bool
    timesteps: int
    model_path: str | None
    replay_buffer_path: str | None
    validation: dict
    test: dict
    data_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int
    latest_data_time: str | None
    execution_authority: str = "NONE"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ComponentRunV240:
    component: str
    status: str
    returncode: int
    stdout_tail: str = ""
    stderr_tail: str = ""
    execution_authority: str = "NONE"

    def as_dict(self) -> dict:
        return asdict(self)


__all__ = [
    "AgentStateV240",
    "AgentSpecV240",
    "RetrainDecisionV240",
    "TrainingResultV240",
    "ComponentRunV240",
]
