from __future__ import annotations
import math
import numpy as np, pandas as pd
from .gem_contracts_v2_35_1 import GemScreenerPolicyV2351
from .gem_risk_flags_v2_35_1 import liquidity_quality, risk_penalty

def portfolio_fit_score(
    frame: pd.DataFrame,
    *,
    current_sector_exposure: dict[str,float] | None=None,
    current_industry_exposure: dict[str,float] | None=None,
    sector_cap: float=0.35,
    industry_cap: float=0.25,
) -> pd.Series:
    sectors=current_sector_exposure or {}; industries=current_industry_exposure or {}
    values=[]
    for row in frame.itertuples(index=False):
        sector=str(getattr(row,"sector","UNKNOWN")).upper()
        industry=str(getattr(row,"industry","UNKNOWN")).upper()
        sh=max(0.0,sector_cap-float(sectors.get(sector,0.0)))/max(sector_cap,1e-12)
        ih=max(0.0,industry_cap-float(industries.get(industry,0.0)))/max(industry_cap,1e-12)
        values.append(float(np.clip(0.6*sh+0.4*ih,0,1)))
    return pd.Series(values,index=frame.index,dtype=float)

def weighted_geometric_components(components: pd.DataFrame, policy: GemScreenerPolicyV2351) -> pd.Series:
    out=[]
    eps=0.05
    for idx,row in components.iterrows():
        logs=0.0; used=0.0
        for name,weight in policy.weights.items():
            value=row.get(name,np.nan)
            coverage=row.get(f"{name}_coverage",0.0)
            if np.isfinite(value) and float(coverage)>=policy.min_component_coverage:
                logs += float(weight)*math.log(eps+(1-eps)*float(np.clip(value,0,1)))
                used += float(weight)
        out.append(np.nan if used<0.55 else float(math.exp(logs/used)))
    return pd.Series(out,index=components.index,dtype=float)

def final_gem_score(
    frame: pd.DataFrame,
    components: pd.DataFrame,
    *,
    policy: GemScreenerPolicyV2351 | None=None,
    current_sector_exposure: dict[str,float] | None=None,
    current_industry_exposure: dict[str,float] | None=None,
) -> pd.DataFrame:
    cfg=policy or GemScreenerPolicyV2351()
    base=weighted_geometric_components(components,cfg)
    liquidity=liquidity_quality(frame)
    dq=pd.to_numeric(frame.get("data_quality_score",0.0),errors="coerce").fillna(0).clip(0,1)
    fit=portfolio_fit_score(frame,current_sector_exposure=current_sector_exposure,current_industry_exposure=current_industry_exposure)
    penalty=risk_penalty(frame)
    raw=base*(0.75+0.10*liquidity+0.10*dq+0.05*fit)*(1-penalty)
    out=components.copy()
    out["balance_score"]=base
    out["liquidity_quality"]=liquidity
    out["portfolio_fit"]=fit
    out["risk_penalty"]=penalty
    out["gem_score"]=(100*raw).clip(0,100)
    return out

__all__=["final_gem_score","portfolio_fit_score","weighted_geometric_components"]
