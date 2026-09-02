from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Mapping
import math

AUTHORITY_NONE = "NONE"

@dataclass(frozen=True)
class PortfolioControlPolicyV238:
    max_total_exposure: float = 0.75
    max_strategy_weight: float = 0.25
    max_family_weight: float = 0.35
    max_cluster_weight: float = 0.35
    max_one_way_turnover: float = 0.30
    max_portfolio_heat: float = 0.04
    minimum_cash: float = 0.10
    long_only: bool = True
    leverage: bool = False
    v233_acceptance_required: bool = True
    execution_authority: str = AUTHORITY_NONE
    def __post_init__(self):
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("RL control cannot grant execution authority")
        if not self.long_only or self.leverage:
            raise ValueError("v2.38 research controller is long-only and unlevered")
        for name in ("max_total_exposure","max_strategy_weight","max_family_weight","max_cluster_weight","max_one_way_turnover","max_portfolio_heat","minimum_cash"):
            value=float(getattr(self,name))
            if not math.isfinite(value) or value < 0 or value > 1:
                raise ValueError(f"{name} must be in [0,1]")
        if self.max_total_exposure > 1.0 - self.minimum_cash + 1e-12:
            raise ValueError("max_total_exposure conflicts with minimum_cash")

@dataclass(frozen=True)
class RewardPolicyV238:
    log_wealth_weight: float = 1.0
    turnover_penalty: float = 0.05
    action_jerk_penalty: float = 0.025
    drawdown_increment_penalty: float = 1.0
    tail_risk_penalty: float = 0.20
    concentration_penalty: float = 0.05
    cost_penalty: float = 0.0
    alpha_alignment_bonus: float = 0.01
    reward_clip: float = 5.0

@dataclass(frozen=True)
class ProjectedPortfolioActionV238:
    weights: Mapping[str,float]
    cash_weight: float
    gross_exposure: float
    one_way_turnover: float
    portfolio_heat: float
    blockers: tuple[str,...]
    projection_applied: bool
    execution_authority: str = AUTHORITY_NONE
    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class PortfolioRewardBreakdownV238:
    reward: float
    net_log_return: float
    turnover_penalty: float
    action_jerk_penalty: float
    drawdown_increment_penalty: float
    tail_risk_penalty: float
    concentration_penalty: float
    cost_penalty: float
    alpha_alignment_bonus: float
    execution_authority: str = AUTHORITY_NONE
    def as_dict(self): return asdict(self)

__all__=["AUTHORITY_NONE","PortfolioControlPolicyV238","RewardPolicyV238","ProjectedPortfolioActionV238","PortfolioRewardBreakdownV238"]
