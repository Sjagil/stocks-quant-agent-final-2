from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np

@dataclass(frozen=True)
class MultiAgentRewardMixV238:
    rewards: tuple[float,...]
    global_component: float
    local_components: tuple[float,...]
    difference_components: tuple[float,...]
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def mix_mappo_rewards(global_reward: float, local_rewards, difference_rewards, *, global_weight:float=.70, local_weight:float=.20, difference_weight:float=.10)->MultiAgentRewardMixV238:
    l=np.asarray(local_rewards,dtype=float); d=np.asarray(difference_rewards,dtype=float)
    if l.shape!=d.shape or l.ndim!=1: raise ValueError("local/difference rewards must be equal 1D arrays")
    if not np.isclose(global_weight+local_weight+difference_weight,1.0): raise ValueError("reward weights must sum to 1")
    out=global_weight*float(global_reward)+local_weight*l+difference_weight*d
    return MultiAgentRewardMixV238(tuple(float(x) for x in out),float(global_reward),tuple(map(float,l)),tuple(map(float,d)))

__all__=["MultiAgentRewardMixV238","mix_mappo_rewards"]
