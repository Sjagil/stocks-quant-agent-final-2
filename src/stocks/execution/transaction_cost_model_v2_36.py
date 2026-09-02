from __future__ import annotations
from .cost_contracts_v2_36 import (
    CostEstimateV236, ExecutionCostPolicyV236, MarketStateV236, OrderIntentV236, OrderStyle
)
from .liquidity_state_v2_36 import assess_liquidity
from .market_impact_v2_36 import square_root_market_impact_bps
from .slippage_v2_36 import expected_limit_fill_probability, expected_slippage_bps

def estimate_execution_cost(
    intent: OrderIntentV236,
    state: MarketStateV236,
    *,
    policy: ExecutionCostPolicyV236 | None = None,
) -> CostEstimateV236:
    cfg = policy or ExecutionCostPolicyV236()
    if intent.symbol != state.symbol:
        raise ValueError("intent/state symbol mismatch")
    liquidity = assess_liquidity(intent.notional, state, cfg)
    commission_amount = max(cfg.minimum_commission, intent.notional * cfg.commission_bps / 10000.0)
    commission_bps = commission_amount / intent.notional * 10000.0
    spread_bps = state.spread_bps / 2.0
    if intent.order_style is OrderStyle.LIMIT:
        spread_bps *= max(0.0, 1.0 - cfg.limit_spread_capture_fraction)
    slippage_bps = expected_slippage_bps(
        intent.notional, state, urgency=intent.urgency, order_style=intent.order_style, policy=cfg
    )
    impact_bps = square_root_market_impact_bps(intent.notional, state, urgency=intent.urgency, policy=cfg)
    if intent.order_style is OrderStyle.LIMIT:
        impact_bps *= 0.60
    fx_bps = state.fx_conversion_bps if state.currency != cfg.base_currency else 0.0
    total_bps = (
        commission_bps + cfg.exchange_fees_bps + spread_bps
        + slippage_bps + impact_bps + fx_bps
    )
    fill_probability = (
        1.0 if intent.order_style is OrderStyle.MARKET
        else expected_limit_fill_probability(intent.notional, state, urgency=intent.urgency, policy=cfg)
    )
    blockers = list(liquidity.blockers)
    if intent.order_style is OrderStyle.LIMIT and fill_probability < cfg.minimum_limit_fill_probability:
        blockers.append("LIMIT_FILL_PROBABILITY_LOW")
    return CostEstimateV236(
        symbol=intent.symbol,
        notional=float(intent.notional),
        order_style=intent.order_style.value,
        commission_bps=float(commission_bps),
        exchange_fees_bps=float(cfg.exchange_fees_bps),
        spread_bps=float(spread_bps),
        slippage_bps=float(slippage_bps),
        market_impact_bps=float(impact_bps),
        fx_bps=float(fx_bps),
        total_cost_bps=float(total_bps),
        total_cost_amount=float(intent.notional * total_bps / 10000.0),
        participation_rate=float(liquidity.participation_rate),
        expected_fill_probability=float(fill_probability),
        expected_filled_notional=float(intent.notional * fill_probability),
        liquidity_bucket=liquidity.bucket,
        capacity_notional=float(liquidity.capacity_notional),
        blockers=tuple(dict.fromkeys(blockers)),
    )

def estimate_round_trip_cost_bps(
    intent: OrderIntentV236,
    state: MarketStateV236,
    *,
    exit_multiplier: float = 1.0,
    policy: ExecutionCostPolicyV236 | None = None,
) -> float:
    entry = estimate_execution_cost(intent, state, policy=policy).total_cost_bps
    return float(entry * (1.0 + max(float(exit_multiplier), 0.0)))

__all__ = ["estimate_execution_cost", "estimate_round_trip_cost_bps"]
