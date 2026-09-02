from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class EdgeCostStressV236:
    multiple: float
    stressed_cost_bps: float
    net_edge_bps: float
    positive: bool
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def stress_executable_edge(
    gross_edge_bps: float,
    base_cost_bps: float,
    multiples = (1.0, 1.5, 2.0, 3.0),
) -> tuple[EdgeCostStressV236, ...]:
    rows = []
    for multiple in multiples:
        cost = max(float(base_cost_bps), 0.0) * float(multiple)
        net = float(gross_edge_bps) - cost
        rows.append(EdgeCostStressV236(float(multiple), float(cost), float(net), bool(net > 0)))
    return tuple(rows)

__all__ = ["EdgeCostStressV236", "stress_executable_edge"]
