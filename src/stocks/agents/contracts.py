from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentVote:
    agent: str
    role: str
    symbol: str
    action: str
    target_exposure: float | None = None
    confidence: float = 0.0
    modifier: float = 1.0
    model_id: str | None = None
    available: bool = True
    reason: str | None = None
    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentDecisionEnvelope:
    symbol: str
    hard_gates_pass: bool
    timing_action: str
    sac_target_exposure: float
    risk_capped_exposure: float
    nlp_modifier: float
    shadow_target_exposure: float
    votes: tuple[AgentVote, ...]
    blockers: tuple[str, ...]
    money_control: bool = False
    broker_calls: int = 0
    order_calls: int = 0
    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["votes"] = [
            vote.to_dict()
            for vote in self.votes
        ]
        return payload
