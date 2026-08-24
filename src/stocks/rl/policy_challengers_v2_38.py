from __future__ import annotations
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class AlgorithmSpecV238:
    algorithm:str; role:str; on_policy:bool; centralized_critic:bool; execution_authority:str="NONE"
    def as_dict(self): return asdict(self)

def challenger_specs()->tuple[AlgorithmSpecV238,...]:
    return (
      AlgorithmSpecV238("PPO","PRIMARY_PORTFOLIO_CONTROLLER",True,False),
      AlgorithmSpecV238("SAC","CONTINUOUS_CONTROL_CHALLENGER",False,False),
      AlgorithmSpecV238("MAPPO","MULTI_AGENT_CHALLENGER",True,True),
    )

def build_sb3_model(algorithm:str, env, **kwargs):
    name=str(algorithm).upper()
    if name not in {"PPO","SAC"}: raise ValueError("SB3 builder supports PPO or SAC")
    try:
        from stable_baselines3 import PPO,SAC
    except Exception as exc:
        raise ImportError("stable-baselines3 required; install the rl extra") from exc
    cls=PPO if name=="PPO" else SAC
    defaults={"verbose":0,"seed":38}
    defaults.update(kwargs)
    return cls("MlpPolicy",env,**defaults)

__all__=["AlgorithmSpecV238","challenger_specs","build_sb3_model"]
