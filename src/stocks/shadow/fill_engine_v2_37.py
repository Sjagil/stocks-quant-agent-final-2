from __future__ import annotations
import hashlib

from stocks.execution.cost_contracts_v2_36 import OrderIntentV236, OrderStyle, Side
from stocks.execution.partial_fill_v2_36 import simulate_partial_fills
from stocks.execution.transaction_cost_model_v2_36 import estimate_execution_cost
from .contracts_v2_37 import ShadowFillV237, ShadowSide
from .idempotency_v2_37 import deterministic_identifier

def deterministic_shadow_fill(
    *,
    order_id: str,
    symbol: str,
    side: ShadowSide,
    requested_notional: float,
    market_state,
    fill_time: str,
    order_style: str = "MARKET",
    urgency: float = 0.5,
    remaining_notional: float | None = None,
    target_quantity: float | None = None,
    force_fill_fraction: float | None = None,
) -> ShadowFillV237:
    style = OrderStyle(str(order_style))
    intent = OrderIntentV236(
        symbol,
        float(remaining_notional if remaining_notional is not None else requested_notional),
        Side.BUY if side is ShadowSide.BUY else Side.SELL,
        style,
        float(urgency),
    )
    estimate = estimate_execution_cost(intent, market_state)
    if force_fill_fraction is None:
        seed = int(hashlib.sha256(order_id.encode()).hexdigest()[:8], 16)
        sim = simulate_partial_fills(intent, market_state, simulations=500, seed=seed)
        fraction = float(sim.p50_fill_fraction)
    else:
        fraction = float(force_fill_fraction)
    fraction = min(max(fraction, 0.0), 1.0)
    progress_notional = intent.notional * fraction
    if progress_notional <= 0:
        raise ValueError("fill fraction produced zero notional")
    adverse_bps = estimate.spread_bps + estimate.slippage_bps + estimate.market_impact_bps
    sign = 1.0 if side is ShadowSide.BUY else -1.0
    fill_price = float(market_state.price) * (1.0 + sign * adverse_bps / 10000.0)
    if target_quantity is None:
        quantity = progress_notional / fill_price
    else:
        quantity = float(target_quantity) * fraction
    executed_notional = quantity * fill_price
    explicit_bps = estimate.commission_bps + estimate.exchange_fees_bps + estimate.fx_bps
    explicit_cost = executed_notional * explicit_bps / 10000.0
    implicit_cost = abs(fill_price - float(market_state.price)) * quantity
    fill_id = deterministic_identifier("FILL", f"{order_id}:{fill_time}:{round(progress_notional,8)}")
    return ShadowFillV237(
        fill_id, order_id, symbol, side, quantity, progress_notional, float(market_state.price), fill_price,
        implicit_cost, explicit_cost, estimate.total_cost_bps, fill_time,
    )

__all__ = ["deterministic_shadow_fill"]
