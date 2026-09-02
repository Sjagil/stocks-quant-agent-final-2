from __future__ import annotations
import math
from .cost_contracts_v2_36 import ExecutionCostPolicyV236, MarketStateV236, OrderStyle

def expected_slippage_bps(
    notional: float,
    state: MarketStateV236,
    *,
    urgency: float = 0.5,
    order_style: OrderStyle = OrderStyle.MARKET,
    policy: ExecutionCostPolicyV236 | None = None,
) -> float:
    cfg = policy or ExecutionCostPolicyV236()
    participation = max(float(notional) / state.adv20_notional, 0.0)
    vol_bps = state.daily_volatility * 10000.0
    slippage = cfg.base_slippage_bps
    slippage += cfg.volatility_coefficient * vol_bps * math.sqrt(participation)
    slippage += cfg.participation_coefficient * participation
    slippage *= state.time_of_day_factor * (0.75 + 0.50 * urgency)
    slippage *= 1.0 + 0.75 * (1.0 - state.liquidity_score)
    if order_style is OrderStyle.LIMIT:
        slippage *= 0.45
    return float(max(slippage, 0.0))

def expected_limit_fill_probability(
    notional: float,
    state: MarketStateV236,
    *,
    urgency: float = 0.5,
    policy: ExecutionCostPolicyV236 | None = None,
) -> float:
    cfg = policy or ExecutionCostPolicyV236()
    participation = max(float(notional) / state.adv20_notional, 0.0)
    spread_term = min(state.spread_bps / 100.0, 1.0)
    capacity_term = min(participation / max(cfg.max_participation_rate, 1e-12), 2.0)
    probability = (
        0.88
        - 0.28 * spread_term
        - 0.30 * capacity_term
        - cfg.queue_penalty
        + 0.15 * urgency
        + 0.10 * state.liquidity_score
    )
    return float(min(max(probability, 0.05), 0.98))

__all__ = ["expected_limit_fill_probability", "expected_slippage_bps"]
