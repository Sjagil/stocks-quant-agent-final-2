from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
import math

AUTHORITY_NONE = "NONE"

class OrderStyle(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class LiquidityBucket(str, Enum):
    DEEP = "DEEP"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"

@dataclass(frozen=True)
class MarketStateV236:
    symbol: str
    price: float
    spread_bps: float
    adv20_notional: float
    daily_volatility: float
    liquidity_score: float = 1.0
    data_quality_score: float = 1.0
    time_of_day_factor: float = 1.0
    currency: str = "EUR"
    fx_conversion_bps: float = 0.0

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("symbol required")
        for name in ("price", "adv20_notional"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive")
        if not math.isfinite(float(self.spread_bps)) or self.spread_bps < 0:
            raise ValueError("spread_bps invalid")
        if not math.isfinite(float(self.daily_volatility)) or not 0 <= self.daily_volatility <= 5:
            raise ValueError("daily_volatility invalid")
        if not 0 <= self.liquidity_score <= 1 or not 0 <= self.data_quality_score <= 1:
            raise ValueError("scores in [0,1]")
        if self.time_of_day_factor <= 0:
            raise ValueError("time_of_day_factor positive")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "currency", self.currency.strip().upper())

@dataclass(frozen=True)
class OrderIntentV236:
    symbol: str
    notional: float
    side: Side = Side.BUY
    order_style: OrderStyle = OrderStyle.MARKET
    urgency: float = 0.5

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("symbol required")
        if not math.isfinite(float(self.notional)) or self.notional <= 0:
            raise ValueError("notional positive")
        if not 0 <= self.urgency <= 1:
            raise ValueError("urgency in [0,1]")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())

@dataclass(frozen=True)
class ExecutionCostPolicyV236:
    base_currency: str = "EUR"
    minimum_commission: float = 0.35
    commission_bps: float = 0.0
    exchange_fees_bps: float = 0.0
    base_slippage_bps: float = 0.5
    volatility_coefficient: float = 0.06
    participation_coefficient: float = 12.0
    square_root_impact_coefficient: float = 0.35
    max_impact_bps: float = 250.0
    max_adv_fraction: float = 0.05
    max_participation_rate: float = 0.10
    minimum_adv_notional: float = 1_000_000.0
    minimum_data_quality: float = 0.70
    limit_spread_capture_fraction: float = 0.50
    minimum_limit_fill_probability: float = 0.35
    queue_penalty: float = 0.10
    minimum_net_edge_bps: float = 5.0
    minimum_edge_to_cost_ratio: float = 1.25
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self):
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("cannot grant execution authority")
        if self.minimum_commission < 0 or self.max_impact_bps <= 0:
            raise ValueError("invalid cost policy")
        for value in (
            self.max_adv_fraction, self.max_participation_rate, self.minimum_data_quality,
            self.limit_spread_capture_fraction, self.minimum_limit_fill_probability, self.queue_penalty,
        ):
            if not 0 <= value <= 1:
                raise ValueError("fraction policy fields in [0,1]")

@dataclass(frozen=True)
class CostEstimateV236:
    symbol: str
    notional: float
    order_style: str
    commission_bps: float
    exchange_fees_bps: float
    spread_bps: float
    slippage_bps: float
    market_impact_bps: float
    fx_bps: float
    total_cost_bps: float
    total_cost_amount: float
    participation_rate: float
    expected_fill_probability: float
    expected_filled_notional: float
    liquidity_bucket: str
    capacity_notional: float
    blockers: tuple[str, ...] = ()
    execution_authority: str = AUTHORITY_NONE

    def as_dict(self):
        return asdict(self)

__all__ = [
    "AUTHORITY_NONE", "CostEstimateV236", "ExecutionCostPolicyV236", "LiquidityBucket",
    "MarketStateV236", "OrderIntentV236", "OrderStyle", "Side",
]
