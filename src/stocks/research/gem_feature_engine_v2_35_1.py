from __future__ import annotations
import numpy as np
import pandas as pd

def robust_percentile_rank(values: pd.Series, *, higher_is_better: bool=True) -> pd.Series:
    x=pd.to_numeric(values,errors="coerce")
    rank=x.rank(method="average",pct=True)
    return rank if higher_is_better else 1.0-rank+1.0/max(int(x.notna().sum()),1)

def sector_relative_rank(frame: pd.DataFrame, column: str, *, sector_column: str="sector", higher_is_better: bool=True) -> pd.Series:
    if column not in frame: return pd.Series(np.nan,index=frame.index,dtype=float)
    if sector_column not in frame:
        return robust_percentile_rank(frame[column],higher_is_better=higher_is_better)
    out=pd.Series(np.nan,index=frame.index,dtype=float)
    sectors=frame[sector_column].fillna("UNKNOWN").astype(str)
    for _,idx in sectors.groupby(sectors).groups.items():
        local=frame.loc[idx,column]
        if pd.to_numeric(local,errors="coerce").notna().sum()>=3:
            out.loc[idx]=robust_percentile_rank(local,higher_is_better=higher_is_better)
        else:
            out.loc[idx]=robust_percentile_rank(frame[column],higher_is_better=higher_is_better).loc[idx]
    return out.clip(0,1)

def component_score(frame: pd.DataFrame, specs: dict[str,bool], *, sector_column: str="sector") -> tuple[pd.Series,pd.Series]:
    parts=[]
    for col,higher in specs.items():
        if col in frame:
            parts.append(sector_relative_rank(frame,col,sector_column=sector_column,higher_is_better=higher).rename(col))
    if not parts:
        nan=pd.Series(np.nan,index=frame.index,dtype=float)
        return nan,pd.Series(0.0,index=frame.index)
    table=pd.concat(parts,axis=1)
    coverage=table.notna().mean(axis=1)
    score=table.mean(axis=1,skipna=True)
    return score.clip(0,1),coverage

def safe_01(values, *, lo: float=0.0, hi: float=1.0) -> pd.Series:
    x=pd.to_numeric(values,errors="coerce")
    if hi<=lo: raise ValueError("hi must exceed lo")
    return ((x-lo)/(hi-lo)).clip(0,1)
__all__=["component_score","robust_percentile_rank","safe_01","sector_relative_rank"]
