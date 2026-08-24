from __future__ import annotations
import math
import numpy as np
import pandas as pd

def normalize_holdings_weights(values: dict[str,float]) -> dict[str,float]:
    clean={str(k).upper():max(0.0,float(v)) for k,v in values.items() if np.isfinite(v) and float(v)>0}
    total=sum(clean.values())
    return {} if total<=0 else {k:v/total for k,v in clean.items()}

def weighted_holdings_overlap(a: dict[str,float], b: dict[str,float]) -> float:
    aa=normalize_holdings_weights(a); bb=normalize_holdings_weights(b)
    return float(sum(min(aa.get(k,0.0),bb.get(k,0.0)) for k in set(aa)|set(bb)))

def holdings_cosine_similarity(a: dict[str,float], b: dict[str,float]) -> float:
    aa=normalize_holdings_weights(a); bb=normalize_holdings_weights(b); keys=sorted(set(aa)|set(bb))
    if not keys: return float("nan")
    x=np.array([aa.get(k,0.0) for k in keys]); y=np.array([bb.get(k,0.0) for k in keys])
    denom=float(np.linalg.norm(x)*np.linalg.norm(y))
    return float("nan") if denom<=1e-15 else float(x@y/denom)

def holdings_hhi(a: dict[str,float]) -> float:
    aa=normalize_holdings_weights(a)
    return float(sum(v*v for v in aa.values()))

def effective_constituents(a: dict[str,float]) -> float:
    h=holdings_hhi(a)
    return 0.0 if h<=0 else 1.0/h

def pairwise_etf_overlap_matrix(holdings_by_etf: dict[str,dict[str,float]]) -> pd.DataFrame:
    names=sorted(holdings_by_etf)
    out=pd.DataFrame(np.eye(len(names)),index=names,columns=names,dtype=float)
    for i,a in enumerate(names):
        for j in range(i+1,len(names)):
            b=names[j]; value=weighted_holdings_overlap(holdings_by_etf[a],holdings_by_etf[b])
            out.loc[a,b]=out.loc[b,a]=value
    return out

__all__=["effective_constituents","holdings_cosine_similarity","holdings_hhi","normalize_holdings_weights","pairwise_etf_overlap_matrix","weighted_holdings_overlap"]
