from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

SHA256_LENGTH = 64


class IntentAction(str, Enum):
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    HOLD = "HOLD"
    EXIT = "EXIT"


@dataclass(frozen=True)
class TradeIntent:
    """Execution-neutral contract handed to the repository's existing risk/execution engine.

    This object is deliberately not an IBKR order. It contains desired portfolio
    state plus provenance so a separate authority layer can accept, resize, reject
    or translate it.
    """

    created_at: datetime
    symbol: str
    action: IntentAction
    target_weight: float
    target_notional_eur: float
    confidence: float
    source: str = "portfolio_plan"
    execution_authority: str = "NONE"
    rationale: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    intent_id: str | None = None

    def __post_init__(self) -> None:
        if self.execution_authority != "NONE":
            raise ValueError("TradeIntent must remain execution-neutral")
        if not 0.0 <= self.target_weight <= 1.0:
            raise ValueError("target_weight must be between 0 and 1")
        if self.target_notional_eur < 0:
            raise ValueError("target_notional_eur cannot be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.intent_id is not None:
            normalized = self.intent_id.strip().lower()
            if len(normalized) != SHA256_LENGTH or any(
                character not in "0123456789abcdef" for character in normalized
            ):
                raise ValueError("intent_id must be a SHA-256 hex digest")
            object.__setattr__(self, "intent_id", normalized)
