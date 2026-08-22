from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class ParameterRobustness:
    neighbor_count: int
    center_score: float
    median_neighbor_score: float
    median_ratio: float
    positive_fraction: float
    cliff_fraction: float
    robustness_score: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)


def parameter_neighborhood_robustness(center_score: float, neighbor_scores, *, cliff_ratio: float = 0.50) -> ParameterRobustness:
    n=np.asarray(list(neighbor_scores),dtype=float); n=n[np.isfinite(n)]
    if len(n)==0: raise ValueError("neighbor scores required")
    center=float(center_score); med=float(np.median(n))
    denom=max(abs(center),1e-12); ratio=float(np.clip(med/denom,-2,2))
    positive=float(np.mean(n>0)); cliff=float(np.mean(n < center*cliff_ratio)) if center>0 else 0.0
    score=float(np.clip(0.45*max(0,min(1,ratio))+0.35*positive+0.20*(1-cliff),0,1))
    return ParameterRobustness(len(n),center,med,ratio,positive,cliff,score)


__all__=["ParameterRobustness","parameter_neighborhood_robustness"]
