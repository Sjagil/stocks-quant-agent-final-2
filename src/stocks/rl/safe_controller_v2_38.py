from __future__ import annotations
from dataclasses import dataclass,asdict
import pandas as pd
from .action_projection_v2_38 import project_portfolio_action
from .control_contracts_v2_38 import PortfolioControlPolicyV238

@dataclass(frozen=True)
class RLShadowTargetV238:
    status:str; weights:dict[str,float]; cash_weight:float; blockers:tuple[str,...]; source:str="RL_CHALLENGER"; execution_authority:str="NONE"
    def as_dict(self): return asdict(self)

def rl_action_to_shadow_target(raw_weights:pd.Series, *, current_weights:pd.Series, accepted_mask:pd.Series, reconciliation_status:str, family:dict[str,str]|None=None, cluster:dict[str,str]|None=None, stop_distance:pd.Series|None=None, policy:PortfolioControlPolicyV238|None=None)->RLShadowTargetV238:
    if reconciliation_status!="READY": return RLShadowTargetV238("BLOCKED_RECONCILIATION",{},1.0,("SHADOW_RECONCILIATION_NOT_READY",))
    p=project_portfolio_action(raw_weights,current_weights=current_weights,accepted_mask=accepted_mask,family=family,cluster=cluster,stop_distance=stop_distance,policy=policy)
    return RLShadowTargetV238("SHADOW_TARGET_ONLY",dict(p.weights),p.cash_weight,p.blockers)

__all__=["RLShadowTargetV238","rl_action_to_shadow_target"]
