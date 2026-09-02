from __future__ import annotations
from dataclasses import dataclass, asdict
import pandas as pd, numpy as np

@dataclass(frozen=True)
class ShadowTransitionDatasetV238:
    frame: pd.DataFrame
    rows:int
    symbols:tuple[str,...]
    strategies:tuple[str,...]
    causal:bool=True
    execution_authority:str="NONE"
    def as_dict(self): return {"rows":self.rows,"symbols":self.symbols,"strategies":self.strategies,"causal":self.causal,"execution_authority":self.execution_authority}

def build_shadow_transition_dataset(events: pd.DataFrame)->ShadowTransitionDatasetV238:
    required={"decision_time","outcome_time","symbol","strategy_id","state_features","action_weight","realized_net_return","realized_cost_bps"}
    missing=required-set(events.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    f=events.copy()
    f["decision_time"]=pd.to_datetime(f.decision_time,utc=True,errors="raise"); f["outcome_time"]=pd.to_datetime(f.outcome_time,utc=True,errors="raise")
    if (f.outcome_time<=f.decision_time).any(): raise AssertionError("outcome must be strictly after decision time")
    f=f.sort_values(["decision_time","symbol","strategy_id"]).reset_index(drop=True)
    for c in ("action_weight","realized_net_return","realized_cost_bps"):
        f[c]=pd.to_numeric(f[c],errors="coerce")
    if not np.isfinite(f[["action_weight","realized_net_return","realized_cost_bps"]].to_numpy()).all(): raise ValueError("numeric transition fields finite")
    return ShadowTransitionDatasetV238(f,len(f),tuple(sorted(f.symbol.astype(str).unique())),tuple(sorted(f.strategy_id.astype(str).unique())))

__all__=["ShadowTransitionDatasetV238","build_shadow_transition_dataset"]
