from __future__ import annotations
from dataclasses import asdict, dataclass
from .portfolio_diagnostics_v2_34 import PortfolioDiagnosticsV234

@dataclass(frozen=True)
class PortfolioUtilityPolicyV234:
    variance_penalty: float=3.0
    expected_shortfall_penalty: float=0.25
    turnover_penalty: float=0.005
    concentration_penalty: float=0.002

@dataclass(frozen=True)
class PortfolioUtilityV234:
    score: float; expected_return: float; variance_penalty: float; tail_penalty: float; turnover_penalty: float; concentration_penalty: float
    def as_dict(self): return asdict(self)

def portfolio_utility(d: PortfolioDiagnosticsV234, policy: PortfolioUtilityPolicyV234|None=None) -> PortfolioUtilityV234:
    p=policy or PortfolioUtilityPolicyV234(); vp=p.variance_penalty*d.variance; ep=p.expected_shortfall_penalty*d.expected_shortfall_95; tp=p.turnover_penalty*d.turnover; cp=p.concentration_penalty*d.hhi
    return PortfolioUtilityV234(float(d.expected_return-vp-ep-tp-cp),d.expected_return,float(vp),float(ep),float(tp),float(cp))

__all__=["PortfolioUtilityPolicyV234","PortfolioUtilityV234","portfolio_utility"]
