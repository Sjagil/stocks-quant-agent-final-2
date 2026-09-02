from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
from .multiagent_rewards_v2_38 import mix_mappo_rewards

@dataclass(frozen=True)
class MAPPOControlBatchV238:
    local_observations:np.ndarray; global_observations:np.ndarray; eligible_mask:np.ndarray; rewards:np.ndarray; execution_authority:str="NONE"
    def as_dict(self): return {"local_shape":self.local_observations.shape,"global_shape":self.global_observations.shape,"eligible_shape":self.eligible_mask.shape,"reward_shape":self.rewards.shape,"execution_authority":self.execution_authority}

def build_mappo_control_batch(local_observations, global_observations, eligible_mask, global_rewards, local_rewards, difference_rewards)->MAPPOControlBatchV238:
    local=np.asarray(local_observations,dtype=np.float32); glob=np.asarray(global_observations,dtype=np.float32); mask=np.asarray(eligible_mask,dtype=bool)
    if local.ndim!=3: raise ValueError("local observations [time,agent,feature]")
    if glob.ndim!=2 or glob.shape[0]!=local.shape[0]: raise ValueError("global observations [time,feature]")
    if mask.shape!=local.shape[:2]: raise ValueError("eligible mask [time,agent]")
    gr=np.asarray(global_rewards,dtype=float); lr=np.asarray(local_rewards,dtype=float); dr=np.asarray(difference_rewards,dtype=float)
    if gr.shape!=(local.shape[0],) or lr.shape!=local.shape[:2] or dr.shape!=lr.shape: raise ValueError("reward shapes invalid")
    mixed=np.vstack([mix_mappo_rewards(gr[t],lr[t],dr[t]).rewards for t in range(local.shape[0])]).astype(np.float32)
    mixed=np.where(mask,mixed,0.0)
    return MAPPOControlBatchV238(local,glob,mask,mixed)

__all__=["MAPPOControlBatchV238","build_mappo_control_batch"]
