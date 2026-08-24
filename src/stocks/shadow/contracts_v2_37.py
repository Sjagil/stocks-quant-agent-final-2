from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
from datetime import datetime, timezone

AUTHORITY_NONE = "NONE"

class ShadowSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class ShadowOrderStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ShadowPositionStatus(str, Enum):
    OPEN = "OPEN"
    EXIT_PENDING = "EXIT_PENDING"
    CLOSED = "CLOSED"

def _utc_iso(value: str | datetime) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True)
class ShadowDecisionV237:
    decision_id: str
    strategy_id: str
    family: str
    symbol: str
    side: ShadowSide
    target_notional: float
    gross_edge_bps: float
    decision_time: str | datetime
    expected_horizon_bars: int = 40
    stop_loss_pct: float = 0.03
    take_profit_pct: float | None = 0.08
    trailing_stop_pct: float | None = 0.04
    intent: str = "OPEN_OR_ADJUST"
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        for name in ("decision_id", "strategy_id", "family", "symbol"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} required")
        if not math.isfinite(float(self.target_notional)) or self.target_notional <= 0:
            raise ValueError("target_notional must be positive")
        if not math.isfinite(float(self.gross_edge_bps)):
            raise ValueError("gross_edge_bps must be finite")
        if self.expected_horizon_bars < 1:
            raise ValueError("expected_horizon_bars positive")
        if not 0 < float(self.stop_loss_pct) < 1:
            raise ValueError("stop_loss_pct in (0,1)")
        for name in ("take_profit_pct", "trailing_stop_pct"):
            value = getattr(self, name)
            if value is not None and not 0 < float(value) < 5:
                raise ValueError(f"{name} invalid")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("shadow decision cannot grant execution authority")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "decision_time", _utc_iso(self.decision_time))

    def as_dict(self):
        out = asdict(self)
        out["side"] = self.side.value
        return out

@dataclass(frozen=True)
class ShadowFillV237:
    fill_id: str
    order_id: str
    symbol: str
    side: ShadowSide
    quantity: float
    order_progress_notional: float
    reference_price: float
    fill_price: float
    implicit_cost_amount: float
    explicit_cost_amount: float
    predicted_cost_bps: float
    fill_time: str | datetime
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        if self.quantity <= 0 or self.order_progress_notional <= 0 or self.fill_price <= 0 or self.reference_price <= 0:
            raise ValueError("fill quantity/notional/prices positive")
        if self.implicit_cost_amount < 0 or self.explicit_cost_amount < 0 or self.predicted_cost_bps < 0:
            raise ValueError("fill costs non-negative")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("shadow fill cannot grant execution authority")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "fill_time", _utc_iso(self.fill_time))

    @property
    def notional(self) -> float:
        return float(self.quantity * self.fill_price)

    def as_dict(self):
        out = asdict(self)
        out["side"] = self.side.value
        out["notional"] = self.notional
        out["total_implementation_shortfall_amount"] = self.implicit_cost_amount + self.explicit_cost_amount
        return out

@dataclass(frozen=True)
class ExitPolicyV237:
    stop_loss_pct: float = 0.03
    take_profit_pct: float | None = 0.08
    trailing_stop_pct: float | None = 0.04
    max_holding_bars: int = 160
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        if not 0 < self.stop_loss_pct < 1:
            raise ValueError("stop_loss_pct in (0,1)")
        if self.take_profit_pct is not None and self.take_profit_pct <= 0:
            raise ValueError("take_profit_pct positive")
        if self.trailing_stop_pct is not None and not 0 < self.trailing_stop_pct < 1:
            raise ValueError("trailing_stop_pct in (0,1)")
        if self.max_holding_bars < 1:
            raise ValueError("max_holding_bars positive")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("exit policy cannot grant execution authority")

__all__ = [
    "AUTHORITY_NONE", "ExitPolicyV237", "ShadowDecisionV237", "ShadowFillV237",
    "ShadowOrderStatus", "ShadowPositionStatus", "ShadowSide",
]
