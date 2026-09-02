from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np

@dataclass(frozen=True)
class ShrunkMeanV239:
    posterior_mean: float
    observed_mean: float
    observations: int
    prior_mean: float
    prior_strength: float
    standard_error: float | None
    def as_dict(self): return asdict(self)

def shrink_mean(values, *, prior_mean: float=0.0, prior_strength: float=20.0) -> ShrunkMeanV239:
    x=np.asarray(list(values),dtype=float); x=x[np.isfinite(x)]
    n=len(x)
    if prior_strength < 0: raise ValueError("prior_strength >= 0")
    if n==0: return ShrunkMeanV239(float(prior_mean),float('nan'),0,float(prior_mean),float(prior_strength),None)
    mean=float(x.mean()); post=float((n*mean+prior_strength*prior_mean)/(n+prior_strength))
    se=float(x.std(ddof=1)/math.sqrt(n)) if n>1 else None
    return ShrunkMeanV239(post,mean,n,float(prior_mean),float(prior_strength),se)

__all__=["ShrunkMeanV239","shrink_mean"]
