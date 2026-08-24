from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from stocks.research.drift_v2_31 import drift_report

@dataclass(frozen=True)
class DecayReportV239:
    baseline_mean: float
    recent_mean: float
    ratio: float
    slope: float
    severity: float
    def as_dict(self): return asdict(self)

def performance_decay(values, *, recent_fraction: float=0.35, min_points: int=8) -> DecayReportV239:
    x=np.asarray(list(values),dtype=float); x=x[np.isfinite(x)]
    if len(x)<min_points: return DecayReportV239(float('nan'),float('nan'),1.0,0.0,0.0)
    cut=max(2,min(len(x)-2,int(round(len(x)*(1-recent_fraction)))))
    base=x[:cut]; recent=x[cut:]
    bm=float(np.mean(base)); rm=float(np.mean(recent))
    denom=max(abs(bm),1e-9); ratio=rm/denom if bm>=0 else -rm/denom
    slope=float(np.polyfit(np.arange(len(x),dtype=float),x,1)[0]) if len(x)>2 else 0.0
    drop=max(0.0,1.0-ratio) if bm>0 else max(0.0,-rm/denom)
    sign_penalty=0.35 if bm>0 and rm<0 else 0.0
    slope_penalty=min(0.35,max(0.0,-slope*len(x)/denom)) if bm>0 else 0.0
    severity=float(np.clip(0.55*min(drop,1.0)+sign_penalty+slope_penalty,0.0,1.0))
    return DecayReportV239(bm,rm,float(ratio),slope,severity)

def dataframe_drift(reference: pd.DataFrame, current: pd.DataFrame, features=None) -> tuple[pd.DataFrame,float]:
    report=drift_report(reference,current,features=features)
    if report.empty: return report,0.0
    psi=pd.to_numeric(report['psi'],errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
    js=pd.to_numeric(report['js_divergence'],errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
    psi_score=float(np.clip((psi.max() if len(psi) else 0.0)/0.25,0,1))
    js_score=float(np.clip((js.max() if len(js) else 0.0)/0.20,0,1))
    return report,float(max(psi_score,js_score))

__all__=["DecayReportV239","dataframe_drift","performance_decay"]
