from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np

@dataclass(frozen=True)
class RLEvaluationV238:
    net_return:float; sharpe:float; max_drawdown:float; expected_shortfall_95:float; average_turnover:float; average_hhi:float; observations:int; execution_authority:str="NONE"
    def as_dict(self): return asdict(self)

def evaluate_rl_path(net_returns, turnover, hhi)->RLEvaluationV238:
    r=np.asarray(net_returns,dtype=float); t=np.asarray(turnover,dtype=float); c=np.asarray(hhi,dtype=float)
    if r.ndim!=1 or len(r)<2 or len(t)!=len(r) or len(c)!=len(r): raise ValueError("equal 1D paths required")
    wealth=np.cumprod(1+r); peak=np.maximum.accumulate(wealth); dd=1-wealth/np.maximum(peak,1e-12)
    std=float(r.std(ddof=1)); sharpe=float(r.mean()/std*np.sqrt(252)) if std>1e-12 else 0.0
    q=np.quantile(r,.05); es=float(-r[r<=q].mean()) if np.any(r<=q) else 0.0
    return RLEvaluationV238(float(wealth[-1]-1),sharpe,float(dd.max()),max(0.0,es),float(t.mean()),float(c.mean()),len(r))

__all__=["RLEvaluationV238","evaluate_rl_path"]
