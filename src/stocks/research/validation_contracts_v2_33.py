from __future__ import annotations
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ValidationPolicyV233:
    min_observations: int = 60
    min_trades: int = 30
    min_profit_factor: float = 1.05
    min_expectancy: float = 0.0
    min_psr: float = 0.90
    max_pbo: float = 0.50
    min_walkforward_efficiency: float = 0.50
    min_parameter_robustness: float = 0.55
    max_drawdown: float = 0.30
    required_cost_stress_multiple: float = 2.0
    require_cost_stress_positive: bool = True
    require_no_leakage: bool = True
    require_cross_engine_validation: bool = False
    research_compliance_gate_applied: bool = False
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.min_observations < 20 or self.min_trades < 5:
            raise ValueError("validation sample requirements too small")
        if not 0 < self.min_psr < 1 or not 0 <= self.max_pbo <= 1:
            raise ValueError("invalid probability thresholds")
        if self.research_compliance_gate_applied:
            raise ValueError("v2.33 research validation must not apply compliance gate")
        if self.execution_authority != "NONE":
            raise ValueError("validation policy cannot grant execution authority")


@dataclass(frozen=True)
class StrategyValidationDecision:
    strategy_id: str
    status: str
    blockers: tuple[str, ...]
    score: float
    metrics: dict[str, object]
    statistical: dict[str, object]
    robustness: dict[str, object]
    cost_stress: dict[str, object]
    no_leakage: bool
    cross_engine_validated: bool
    research_compliance_gate_applied: bool = False
    broker_submission_enabled: bool = False
    automatic_live_promotion: bool = False
    order_calls: int = 0
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


__all__ = ["StrategyValidationDecision", "ValidationPolicyV233"]
