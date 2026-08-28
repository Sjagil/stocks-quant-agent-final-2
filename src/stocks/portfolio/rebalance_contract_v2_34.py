from __future__ import annotations
from dataclasses import asdict, dataclass
import pandas as pd
from stocks.quant.portfolio_metrics import one_way_turnover

@dataclass(frozen=True)
class RebalanceDecisionV234:
    status: str; turnover: float; max_weight_change: float; utility_improvement: float; blockers: tuple[str,...]; execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def decide_rebalance(current_weights: pd.Series, target_weights: pd.Series, *, current_utility: float, target_utility: float, min_weight_change: float=0.01, min_utility_improvement: float=0.0, max_turnover: float=0.30) -> RebalanceDecisionV234:
    idx=current_weights.index.union(target_weights.index); cur=current_weights.reindex(idx).fillna(0.0); tar=target_weights.reindex(idx).fillna(0.0)
    turnover=float(one_way_turnover(cur,tar)); max_delta=float((tar-cur).abs().max()) if len(idx) else 0.0; improvement=float(target_utility-current_utility); blockers=[]
    if max_delta<min_weight_change: blockers.append("BELOW_NO_TRADE_BAND")
    if improvement<=min_utility_improvement: blockers.append("UTILITY_NOT_IMPROVED")
    if turnover>max_turnover+1e-12: blockers.append("TURNOVER_CAP_EXCEEDED")
    return RebalanceDecisionV234("REBALANCE_SHADOW" if not blockers else "HOLD_SHADOW",turnover,max_delta,improvement,tuple(blockers))

__all__=["RebalanceDecisionV234","decide_rebalance"]
