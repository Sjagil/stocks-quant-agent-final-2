from __future__ import annotations
import math
from .cost_contracts_v2_36 import ExecutionCostPolicyV236, MarketStateV236

def square_root_market_impact_bps(
    notional: float,
    state: MarketStateV236,
    *,
    urgency: float = 0.5,
    policy: ExecutionCostPolicyV236 | None = None,
) -> float:
    cfg = policy or ExecutionCostPolicyV236()
    fraction_adv = max(float(notional), 0.0) / max(state.adv20_notional, 1e-12)
    vol_bps = state.daily_volatility * 10000.0
    urgency_mult = 0.75 + 0.50 * float(urgency)
    liquidity_mult = 1.0 + 1.5 * (1.0 - state.liquidity_score)
    impact = (
        cfg.square_root_impact_coefficient
        * vol_bps
        * math.sqrt(max(fraction_adv, 0.0))
        * urgency_mult
        * liquidity_mult
    )
    return float(min(max(impact, 0.0), cfg.max_impact_bps))

__all__ = ["square_root_market_impact_bps"]
