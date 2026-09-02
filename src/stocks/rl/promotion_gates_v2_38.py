from __future__ import annotations
from dataclasses import dataclass,asdict
from .evaluation_v2_38 import RLEvaluationV238

@dataclass(frozen=True)
class RLPromotionDecisionV238:
    status:str; blockers:tuple[str,...]; challenger_only:bool=True; automatic_live_promotion:bool=False; execution_authority:str="NONE"
    def as_dict(self): return asdict(self)

def evaluate_rl_challenger(candidate:RLEvaluationV238, baseline:RLEvaluationV238, *, min_net_return_improvement:float=0.0, max_drawdown_worsening:float=0.02, max_turnover_ratio:float=1.25, max_es_worsening:float=0.01)->RLPromotionDecisionV238:
    b=[]
    if candidate.net_return < baseline.net_return+min_net_return_improvement: b.append("NO_OOS_NET_RETURN_IMPROVEMENT")
    if candidate.max_drawdown > baseline.max_drawdown+max_drawdown_worsening: b.append("DRAWDOWN_WORSE")
    if candidate.expected_shortfall_95 > baseline.expected_shortfall_95+max_es_worsening: b.append("TAIL_RISK_WORSE")
    if baseline.average_turnover>1e-12 and candidate.average_turnover>baseline.average_turnover*max_turnover_ratio: b.append("TURNOVER_TOO_HIGH")
    return RLPromotionDecisionV238("ELIGIBLE_FORWARD_SHADOW_CHALLENGER" if not b else "REJECT_OR_REWORK",tuple(b))

__all__=["RLPromotionDecisionV238","evaluate_rl_challenger"]
