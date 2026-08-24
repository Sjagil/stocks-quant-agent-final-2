from __future__ import annotations
import numpy as np

def robust_disagreement(values, *, floor: float=0.10) -> float:
    x=np.asarray(list(values),dtype=float); x=x[np.isfinite(x)]
    if len(x)<2: return 0.0
    med=float(np.median(x)); mad=float(np.median(np.abs(x-med)))
    scale=max(abs(med),float(floor))
    return float(np.clip(1.4826*mad/scale,0.0,1.0))

__all__=["robust_disagreement"]
