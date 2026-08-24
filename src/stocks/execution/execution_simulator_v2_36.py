from __future__ import annotations
from dataclasses import asdict, dataclass

from .break_even_v2_36 import executable_edge_gate
from .cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from .cost_stress_v2_36 import stress_executable_edge
from .execution_style_compare_v2_36 import compare_execution_styles
from .market_state_stress_v2_36 import execution_stress_states
from .partial_fill_v2_36 import simulate_partial_fills
from .transaction_cost_model_v2_36 import estimate_execution_cost, estimate_round_trip_cost_bps

@dataclass(frozen=True)
class ExecutionResearchBundleV236:
    one_way_cost: dict[str, object]
    round_trip_cost_bps: float
    edge_decision: dict[str, object]
    style_comparison: dict[str, object]
    partial_fill: dict[str, object]
    cost_multiple_stress: tuple[dict[str, object], ...]
    market_state_stress: tuple[dict[str, object], ...]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def simulate_execution(
    intent: OrderIntentV236,
    state: MarketStateV236,
    *,
    gross_edge_bps: float,
) -> ExecutionResearchBundleV236:
    one_way = estimate_execution_cost(intent, state)
    round_trip = estimate_round_trip_cost_bps(intent, state)
    edge = executable_edge_gate(
        gross_edge_bps=gross_edge_bps,
        expected_cost_bps=round_trip,
        hard_blockers=one_way.blockers,
    )
    styles = compare_execution_styles(intent, state, gross_edge_bps=gross_edge_bps)
    fills = simulate_partial_fills(intent, state, simulations=500, seed=36)
    cost_stress = stress_executable_edge(gross_edge_bps, round_trip)
    market_stress = []
    for name, stressed_state in execution_stress_states(state).items():
        estimate = estimate_execution_cost(intent, stressed_state)
        stressed_round_trip = estimate.total_cost_bps * 2.0
        decision = executable_edge_gate(
            gross_edge_bps=gross_edge_bps,
            expected_cost_bps=stressed_round_trip,
            hard_blockers=estimate.blockers,
        )
        market_stress.append({
            "scenario": name,
            "round_trip_cost_bps": stressed_round_trip,
            "net_edge_bps": decision.net_edge_bps,
            "status": decision.status,
            "blockers": list(decision.blockers),
        })
    return ExecutionResearchBundleV236(
        one_way.as_dict(),
        round_trip,
        edge.as_dict(),
        styles.as_dict(),
        fills.as_dict(),
        tuple(item.as_dict() for item in cost_stress),
        tuple(market_stress),
    )

__all__ = ["ExecutionResearchBundleV236", "simulate_execution"]
