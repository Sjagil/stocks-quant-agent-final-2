from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class WalkForwardDiagnostics:
    folds: int
    positive_oos_fraction: float
    walkforward_efficiency: float | None
    generalization_ratio: float | None
    oos_mean: float
    oos_std: float
    stability_score: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)


def walkforward_diagnostics(is_metrics, oos_metrics) -> WalkForwardDiagnostics:
    ins=np.asarray(list(is_metrics),dtype=float); oos=np.asarray(list(oos_metrics),dtype=float)
    mask=np.isfinite(ins)&np.isfinite(oos); ins=ins[mask]; oos=oos[mask]
    if len(oos)==0: raise ValueError("no finite folds")
    positive=float(np.mean(oos>0)); mean_is=float(np.mean(ins)); mean_oos=float(np.mean(oos))
    wfe=None if abs(mean_is)<=1e-15 else mean_oos/mean_is
    generalization=None if abs(np.median(ins))<=1e-15 else float(np.median(oos)/np.median(ins))
    std=float(np.std(oos,ddof=1)) if len(oos)>1 else 0.0
    consistency=1.0/(1.0+std/(abs(mean_oos)+1e-12))
    stability=float(np.clip(0.5*positive+0.5*consistency,0,1))
    return WalkForwardDiagnostics(len(oos),positive,None if wfe is None else float(wfe),generalization,mean_oos,std,stability)


__all__=["WalkForwardDiagnostics","walkforward_diagnostics"]
