from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
from stocks.quant.portfolio_metrics import profit_factor, trade_expectancy
from .return_distribution_v2_33 import clean_returns


@dataclass(frozen=True)
class CostStressScenario:
    multiple: float
    expectancy: float
    profit_factor: float
    positive: bool
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)


def cost_stress_trade_returns(gross_trade_returns, *, baseline_round_trip_cost_bps: float, multiples=(1.0,1.5,2.0,3.0)) -> tuple[CostStressScenario,...]:
    gross=clean_returns(gross_trade_returns); base=float(baseline_round_trip_cost_bps)/10000.0
    rows=[]
    for multiple in multiples:
        net=gross-base*float(multiple); exp=trade_expectancy(net); pf=profit_factor(net)
        rows.append(CostStressScenario(float(multiple),float(exp),float(pf),bool(np.isfinite(exp) and exp>0)))
    return tuple(rows)


__all__=["CostStressScenario","cost_stress_trade_returns"]
