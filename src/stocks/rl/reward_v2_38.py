from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .control_contracts_v2_38 import RewardPolicyV238, PortfolioRewardBreakdownV238

def portfolio_control_reward(
    *, previous_equity: float,new_equity: float,peak_equity: float,
    weights: pd.Series,previous_weights: pd.Series,previous_action: pd.Series | None=None,
    expected_shortfall: float=0.0,implementation_cost_rate: float=0.0,
    expected_edge: pd.Series | None=None,policy: RewardPolicyV238 | None=None,
) -> PortfolioRewardBreakdownV238:
    cfg=policy or RewardPolicyV238()
    if min(previous_equity,new_equity,peak_equity)<=0: raise ValueError("equity values positive")
    idx=weights.index.union(previous_weights.index)
    w=pd.to_numeric(weights,errors="coerce").reindex(idx).fillna(0.0).clip(lower=0.0)
    pw=pd.to_numeric(previous_weights,errors="coerce").reindex(idx).fillna(0.0).clip(lower=0.0)
    turnover=0.5*float((w-pw).abs().sum())
    pa=pw if previous_action is None else pd.to_numeric(previous_action,errors="coerce").reindex(idx).fillna(0.0)
    jerk=float(((w-pw)-(pw-pa)).abs().sum())
    net_log=math.log(new_equity/previous_equity)
    old_dd=max(0.0,1.0-previous_equity/peak_equity); new_dd=max(0.0,1.0-new_equity/peak_equity)
    dd_inc=max(0.0,new_dd-old_dd)
    hhi=float(np.square(w.to_numpy()).sum())
    tail=max(0.0,float(expected_shortfall)); cost=max(0.0,float(implementation_cost_rate))
    align=0.0
    if expected_edge is not None:
        e=pd.to_numeric(expected_edge,errors="coerce").reindex(idx).fillna(0.0)
        scale=float(e.abs().max())
        if scale>1e-12: align=float((w*(e/scale)).sum())
    terms=dict(
      turnover_penalty=cfg.turnover_penalty*turnover,
      action_jerk_penalty=cfg.action_jerk_penalty*jerk,
      drawdown_increment_penalty=cfg.drawdown_increment_penalty*dd_inc,
      tail_risk_penalty=cfg.tail_risk_penalty*tail,
      concentration_penalty=cfg.concentration_penalty*hhi,
      cost_penalty=cfg.cost_penalty*cost,
      alpha_alignment_bonus=cfg.alpha_alignment_bonus*align,
    )
    reward=cfg.log_wealth_weight*net_log - sum(v for k,v in terms.items() if k!="alpha_alignment_bonus") + terms["alpha_alignment_bonus"]
    reward=float(np.clip(reward,-cfg.reward_clip,cfg.reward_clip))
    return PortfolioRewardBreakdownV238(reward,net_log,**terms)

__all__=["portfolio_control_reward"]
