from __future__ import annotations
import numpy as np
import pandas as pd
from .action_projection_v2_38 import project_portfolio_action
from .control_contracts_v2_38 import PortfolioControlPolicyV238, RewardPolicyV238
from .reward_v2_38 import portfolio_control_reward
try:
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # pragma: no cover
    gym=None; spaces=None

if gym is not None:
  class ShadowPortfolioControlEnvV238(gym.Env):
    metadata={"render_modes":[]}
    def __init__(self, features:pd.DataFrame, strategy_returns:pd.DataFrame, *, accepted_mask:pd.Series, execution_cost_bps:pd.DataFrame|None=None, expected_shortfall:pd.Series|None=None, expected_edge:pd.DataFrame|None=None, stop_distance:pd.Series|None=None, control_policy:PortfolioControlPolicyV238|None=None, reward_policy:RewardPolicyV238|None=None, initial_equity:float=10000.0):
      super().__init__(); self.features=features.astype(float); self.returns=strategy_returns.astype(float).reindex(self.features.index); self.strategies=list(self.returns.columns); self.accepted=accepted_mask.reindex(self.strategies).fillna(False); self.stop_distance=stop_distance; self.cp=control_policy or PortfolioControlPolicyV238(); self.rp=reward_policy or RewardPolicyV238(); self.initial_equity=float(initial_equity)
      if not self.features.index.equals(self.returns.index) or len(self.features)<3: raise ValueError("aligned features/returns with >=3 rows required")
      self.cost_bps=(pd.DataFrame(0.0,index=self.features.index,columns=self.strategies) if execution_cost_bps is None else execution_cost_bps.reindex(index=self.features.index,columns=self.strategies).fillna(0.0).clip(lower=0.0))
      self.es=(pd.Series(0.0,index=self.features.index) if expected_shortfall is None else pd.to_numeric(expected_shortfall,errors="coerce").reindex(self.features.index).fillna(0.0).clip(lower=0.0))
      self.edge=(None if expected_edge is None else expected_edge.reindex(index=self.features.index,columns=self.strategies).fillna(0.0))
      self.action_space=spaces.Box(0.0,1.0,shape=(len(self.strategies),),dtype=np.float32); self.observation_space=spaces.Box(-np.inf,np.inf,shape=(self.features.shape[1]+len(self.strategies)+3,),dtype=np.float32)
    def _obs(self):
      dd=1-self.eq/max(self.peak,1e-12); return np.concatenate([self.features.iloc[self.t].to_numpy(np.float32),self.weights.to_numpy(np.float32),np.array([self.eq/self.initial_equity,dd,1-self.weights.sum()],np.float32)])
    def reset(self,*,seed=None,options=None):
      super().reset(seed=seed); self.t=0; self.eq=self.initial_equity; self.peak=self.eq; self.weights=pd.Series(0.0,index=self.strategies); self.prev_action=self.weights.copy(); return self._obs(),{"equity":self.eq}
    def step(self,action):
      raw=pd.Series(np.asarray(action,dtype=float),index=self.strategies); proj=project_portfolio_action(raw,current_weights=self.weights,accepted_mask=self.accepted,stop_distance=self.stop_distance,policy=self.cp); target=pd.Series(proj.weights).reindex(self.strategies).fillna(0.0)
      r=self.returns.iloc[self.t+1].reindex(self.strategies).fillna(0.0); delta=(target-self.weights).abs(); cost_rate=float((delta*self.cost_bps.iloc[self.t].reindex(self.strategies).fillna(0.0)/10000.0).sum()); prev=self.eq; gross=float((target*r).sum()); net=gross-cost_rate; self.eq*=max(1e-9,1+net); br=portfolio_control_reward(previous_equity=prev,new_equity=self.eq,peak_equity=self.peak,weights=target,previous_weights=self.weights,previous_action=self.prev_action,expected_shortfall=float(self.es.iloc[self.t]),implementation_cost_rate=cost_rate,expected_edge=None if self.edge is None else self.edge.iloc[self.t],policy=self.rp); self.prev_action=self.weights.copy(); self.weights=target; self.peak=max(self.peak,self.eq); self.t+=1; trunc=self.t>=len(self.features)-2; return self._obs(),br.reward,False,trunc,{"equity":self.eq,"gross_return":gross,"net_return":net,"implementation_cost_rate":cost_rate,"turnover":proj.one_way_turnover,"gross_exposure":proj.gross_exposure,"execution_authority":"NONE"}
else:
  class ShadowPortfolioControlEnvV238:  # pragma: no cover
    def __init__(self,*args,**kwargs): raise ImportError("gymnasium required; install rl extra")

__all__=["ShadowPortfolioControlEnvV238"]
