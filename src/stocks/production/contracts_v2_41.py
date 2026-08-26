from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    OBSERVE = "OBSERVE"
    PAPER = "PAPER"
    LIVE_CANARY = "LIVE_CANARY"


@dataclass(frozen=True)
class ProductionIntent:
    intent_id: str
    symbol: str
    action: str
    quantity: int
    entry_limit: float | None
    stop_price: float | None
    source: str
    rationale: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        action = self.action.strip().upper()
        if action not in {"BUY", "SELL"}:
            raise ValueError("action must be BUY or SELL")
        normalized_intent_id = str(self.intent_id).strip().lower()
        if len(normalized_intent_id) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_intent_id):
            raise ValueError("intent_id must be a SHA-256 hex digest")
        if not symbol:
            raise ValueError("symbol required")
        if int(self.quantity) <= 0:
            raise ValueError("quantity must be positive whole shares")
        if int(self.quantity) != self.quantity:
            raise ValueError("fractional shares are not allowed")
        if self.entry_limit is not None and self.entry_limit <= 0:
            raise ValueError("entry_limit must be positive")
        if self.stop_price is not None and self.stop_price <= 0:
            raise ValueError("stop_price must be positive")
        object.__setattr__(self, "intent_id", normalized_intent_id)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "quantity", int(self.quantity))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreflightReport:
    passed: bool
    mode: str
    gates: dict[str, bool]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerSnapshot:
    connected: bool
    account: str
    environment: str
    net_liquidation: float
    available_funds: float
    total_cash: float
    base_currency: str
    positions: dict[str, float]
    open_orders: tuple[dict[str, Any], ...]
    fills: tuple[dict[str, Any], ...]
    current_time: str
    broker_write_calls: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    bid: float
    ask: float
    last: float | None
    min_tick: float
    observed_at: str

    @property
    def midpoint(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread_bps(self) -> float:
        mid = self.midpoint
        if mid <= 0:
            return float("inf")
        return (self.ask - self.bid) / mid * 10_000.0
