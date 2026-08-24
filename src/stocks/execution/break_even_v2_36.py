from __future__ import annotations
from dataclasses import asdict, dataclass
from collections.abc import Iterable
from .cost_contracts_v2_36 import ExecutionCostPolicyV236

@dataclass(frozen=True)
class ExecutableEdgeDecisionV236:
    status: str
    gross_edge_bps: float
    expected_cost_bps: float
    net_edge_bps: float
    edge_to_cost_ratio: float
    break_even_gross_edge_bps: float
    blockers: tuple[str, ...]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)

def executable_edge_gate(
    *,
    gross_edge_bps: float,
    expected_cost_bps: float,
    hard_blockers: Iterable[str] = (),
    policy: ExecutionCostPolicyV236 | None = None,
) -> ExecutableEdgeDecisionV236:
    cfg = policy or ExecutionCostPolicyV236()
    gross = float(gross_edge_bps)
    cost = max(float(expected_cost_bps), 0.0)
    net = gross - cost
    ratio = float("inf") if cost <= 1e-12 and gross > 0 else gross / max(cost, 1e-12)
    blockers = [str(x) for x in hard_blockers if str(x)]
    if gross <= 0: blockers.append("GROSS_EDGE_NOT_POSITIVE")
    if net < cfg.minimum_net_edge_bps: blockers.append("NET_EDGE_TOO_LOW")
    if ratio < cfg.minimum_edge_to_cost_ratio: blockers.append("EDGE_TO_COST_RATIO_TOO_LOW")
    return ExecutableEdgeDecisionV236(
        "EXECUTABLE_RESEARCH" if not blockers else "REJECT_COSTS",
        gross, cost, net, ratio, float(cost + cfg.minimum_net_edge_bps),
        tuple(dict.fromkeys(blockers)),
    )

__all__ = ["ExecutableEdgeDecisionV236", "executable_edge_gate"]
