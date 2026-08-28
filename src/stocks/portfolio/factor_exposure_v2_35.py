from __future__ import annotations
import numpy as np
import pandas as pd

def estimate_factor_betas(asset_returns, factor_returns: pd.DataFrame, *, min_observations: int = 40) -> pd.Series:
    y=pd.to_numeric(pd.Series(asset_returns),errors="coerce").rename("asset")
    x=factor_returns.apply(pd.to_numeric,errors="coerce")
    joined=pd.concat([y,x],axis=1).dropna()
    if len(joined)<min_observations: return pd.Series({c:np.nan for c in x.columns},dtype=float)
    yy=joined["asset"].to_numpy(float)
    xx=joined[x.columns].to_numpy(float)
    design=np.column_stack([np.ones(len(xx)),xx])
    coef,*_=np.linalg.lstsq(design,yy,rcond=None)
    return pd.Series(coef[1:],index=x.columns,dtype=float)

def portfolio_factor_exposure(weights, factor_exposures: pd.DataFrame) -> pd.Series:
    frame=factor_exposures.apply(pd.to_numeric,errors="coerce").fillna(0.0)
    if isinstance(weights,pd.Series): w=pd.to_numeric(weights,errors="coerce").reindex(frame.index).fillna(0.0)
    else: w=pd.Series(weights,dtype=float).reindex(frame.index).fillna(0.0)
    return frame.mul(w,axis=0).sum(axis=0)

__all__=["estimate_factor_betas","portfolio_factor_exposure"]
