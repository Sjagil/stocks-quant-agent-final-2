from __future__ import annotations
from dataclasses import asdict, dataclass
from .cost_contracts_v2_36 import Side

@dataclass(frozen=True)
class ImplementationShortfallV236:
    decision_price: float
    average_fill_price: float
    filled_notional: float
    explicit_cost_amount: float
    price_shortfall_amount: float
    total_shortfall_amount: float
    total_shortfall_bps: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def realized_implementation_shortfall(
    *,
    decision_price: float,
    average_fill_price: float,
    filled_notional: float,
    explicit_cost_amount: float = 0.0,
    side: Side = Side.BUY,
) -> ImplementationShortfallV236:
    if decision_price <= 0 or average_fill_price <= 0 or filled_notional < 0:
        raise ValueError("invalid shortfall inputs")
    direction = 1.0 if side is Side.BUY else -1.0
    price_move = direction * (average_fill_price / decision_price - 1.0)
    price_amount = filled_notional * price_move
    total = price_amount + float(explicit_cost_amount)
    bps = 0.0 if filled_notional <= 0 else total / filled_notional * 10000.0
    return ImplementationShortfallV236(
        float(decision_price), float(average_fill_price), float(filled_notional),
        float(explicit_cost_amount), float(price_amount), float(total), float(bps),
    )

def expected_shortfall_with_opportunity_cost(
    *,
    execution_cost_bps: float,
    fill_probability: float,
    gross_edge_bps: float,
) -> float:
    probability = min(max(float(fill_probability), 0.0), 1.0)
    return float(
        probability * max(float(execution_cost_bps), 0.0)
        + (1.0 - probability) * max(float(gross_edge_bps), 0.0)
    )

__all__ = [
    "ImplementationShortfallV236",
    "expected_shortfall_with_opportunity_cost",
    "realized_implementation_shortfall",
]
