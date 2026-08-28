from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
from .cost_contracts_v2_36 import MarketStateV236, OrderIntentV236, OrderStyle
from .transaction_cost_model_v2_36 import estimate_execution_cost

@dataclass(frozen=True)
class PartialFillSimulationV236:
    expected_fill_fraction: float
    p10_fill_fraction: float
    p50_fill_fraction: float
    p90_fill_fraction: float
    expected_filled_notional: float
    simulations: int
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def simulate_partial_fills(
    intent: OrderIntentV236,
    state: MarketStateV236,
    *,
    simulations: int = 1000,
    seed: int = 36,
) -> PartialFillSimulationV236:
    if simulations < 100:
        raise ValueError("simulations >=100")
    estimate = estimate_execution_cost(intent, state)
    base = estimate.expected_fill_probability
    mean = min(1.0, base * min(1.0, estimate.capacity_notional / intent.notional))
    concentration = 80.0 if intent.order_style is OrderStyle.MARKET else 18.0
    mean = float(np.clip(mean, 0.01, 0.999))
    a = max(mean * concentration, 0.1)
    b = max((1.0 - mean) * concentration, 0.1)
    rng = np.random.default_rng(seed)
    draws = rng.beta(a, b, size=simulations)
    return PartialFillSimulationV236(
        float(draws.mean()), float(np.quantile(draws, .10)),
        float(np.quantile(draws, .50)), float(np.quantile(draws, .90)),
        float(intent.notional * draws.mean()), simulations,
    )

__all__ = ["PartialFillSimulationV236", "simulate_partial_fills"]
