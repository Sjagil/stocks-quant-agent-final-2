from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np

@dataclass(frozen=True)
class RobustScalerV238:
    median: tuple[float,...]; scale: tuple[float,...]
    def as_dict(self): return asdict(self)

def fit_robust_scaler(x)->RobustScalerV238:
    a=np.asarray(x,dtype=float)
    if a.ndim!=2 or not np.isfinite(a).all(): raise ValueError("finite 2D input required")
    med=np.median(a,axis=0); mad=np.median(np.abs(a-med),axis=0)*1.4826; mad=np.where(mad<1e-8,1.0,mad)
    return RobustScalerV238(tuple(map(float,med)),tuple(map(float,mad)))
def transform_robust(x, scaler:RobustScalerV238, *, clip:float=8.0):
    a=np.asarray(x,dtype=float); med=np.asarray(scaler.median); scale=np.asarray(scaler.scale)
    return np.clip((a-med)/scale,-clip,clip)

__all__=["RobustScalerV238","fit_robust_scaler","transform_robust"]
