from __future__ import annotations
from dataclasses import asdict, dataclass
from .cost_contracts_v2_36 import MarketStateV236, OrderIntentV236, OrderStyle
from .implementation_shortfall_v2_36 import expected_shortfall_with_opportunity_cost
from .transaction_cost_model_v2_36 import estimate_execution_cost

@dataclass(frozen=True)
class ExecutionStyleComparisonV236:
    preferred_style: str
    market_expected_shortfall_bps: float
    limit_expected_shortfall_bps: float
    market_cost_bps: float
    limit_cost_bps: float
    limit_fill_probability: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def compare_execution_styles(
    intent: OrderIntentV236,
    state: MarketStateV236,
    *,
    gross_edge_bps: float,
) -> ExecutionStyleComparisonV236:
    market = estimate_execution_cost(
        OrderIntentV236(intent.symbol, intent.notional, intent.side, OrderStyle.MARKET, intent.urgency),
        state,
    )
    limit = estimate_execution_cost(
        OrderIntentV236(intent.symbol, intent.notional, intent.side, OrderStyle.LIMIT, intent.urgency),
        state,
    )
    market_shortfall = expected_shortfall_with_opportunity_cost(
        execution_cost_bps=market.total_cost_bps,
        fill_probability=market.expected_fill_probability,
        gross_edge_bps=gross_edge_bps,
    )
    limit_shortfall = expected_shortfall_with_opportunity_cost(
        execution_cost_bps=limit.total_cost_bps,
        fill_probability=limit.expected_fill_probability,
        gross_edge_bps=gross_edge_bps,
    )
    preferred = "LIMIT" if limit_shortfall < market_shortfall and not limit.blockers else "MARKET"
    return ExecutionStyleComparisonV236(
        preferred, float(market_shortfall), float(limit_shortfall),
        float(market.total_cost_bps), float(limit.total_cost_bps),
        float(limit.expected_fill_probability),
    )

__all__ = ["ExecutionStyleComparisonV236", "compare_execution_styles"]
