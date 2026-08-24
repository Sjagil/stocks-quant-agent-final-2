from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class ClosedTradeAttributionV237:
    position_id: str
    strategy_id: str
    family: str
    symbol: str
    entry_notional: float
    reference_gross_pnl: float
    fill_pnl: float
    explicit_cost: float
    implementation_shortfall: float
    net_pnl: float
    gross_return_bps: float
    net_return_bps: float
    implementation_shortfall_bps: float
    mfe_bps: float
    mae_bps: float
    bars_held: int
    exit_reason: str
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def attribute_closed_position(position_state) -> ClosedTradeAttributionV237:
    if position_state.status != "CLOSED":
        raise ValueError("position must be CLOSED")
    base = max(float(position_state.entry_notional), 1e-12)
    explicit = float(position_state.entry_explicit_cost_amount + position_state.exit_explicit_cost_amount)
    shortfall = float(position_state.entry_implementation_shortfall_amount + position_state.exit_implementation_shortfall_amount)
    return ClosedTradeAttributionV237(
        position_state.position_id, position_state.strategy_id, position_state.family, position_state.symbol,
        base, float(position_state.realized_reference_gross_pnl), float(position_state.realized_fill_pnl),
        explicit, shortfall, float(position_state.realized_net_pnl),
        float(position_state.realized_reference_gross_pnl / base * 10000.0),
        float(position_state.realized_net_pnl / base * 10000.0),
        float(shortfall / base * 10000.0),
        float(position_state.mfe_bps), float(position_state.mae_bps), int(position_state.bars_held),
        str(position_state.exit_reason or "UNKNOWN"),
    )

__all__ = ["ClosedTradeAttributionV237", "attribute_closed_position"]
