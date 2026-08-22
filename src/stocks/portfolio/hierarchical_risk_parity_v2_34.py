from __future__ import annotations
import numpy as np
import pandas as pd


def _cluster_variance(cov: pd.DataFrame, names: list[str]) -> float:
    sub = cov.loc[names, names].to_numpy(float)
    diagonal = np.clip(np.diag(sub), 1e-18, None)
    ivp = 1.0 / diagonal
    ivp /= ivp.sum()
    return float(ivp @ sub @ ivp)


def _ordered_leaves(covariance: pd.DataFrame) -> list[str]:
    names=list(covariance.columns)
    if len(names) <= 1: return names
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import squareform
    except Exception as exc:  # pragma: no cover
        raise ImportError("scipy is required for HRP") from exc
    std=np.sqrt(np.clip(np.diag(covariance.to_numpy(float)), 1e-18, None))
    corr=covariance.to_numpy(float)/np.outer(std,std)
    corr=np.clip(corr,-1.0,1.0); np.fill_diagonal(corr,1.0)
    dist=np.sqrt(np.clip((1.0-corr)/2.0,0.0,1.0)); np.fill_diagonal(dist,0.0)
    link=linkage(squareform(dist, checks=False), method="single")
    order=leaves_list(link)
    return [names[int(i)] for i in order]


def hierarchical_risk_parity_weights(covariance: pd.DataFrame, *, total_weight: float = 1.0) -> pd.Series:
    if not 0.0 < total_weight <= 1.0: raise ValueError("total_weight must be in (0,1]")
    cov=covariance.astype(float)
    if cov.empty or list(cov.index)!=list(cov.columns): raise ValueError("invalid covariance")
    if not np.isfinite(cov.to_numpy()).all(): raise ValueError("covariance must be finite")
    order=_ordered_leaves(cov)
    weights=pd.Series(1.0,index=order,dtype=float)
    clusters=[order]
    while clusters:
        next_clusters=[]
        for cluster in clusters:
            if len(cluster)<=1: continue
            split=len(cluster)//2; left=cluster[:split]; right=cluster[split:]
            lv=max(_cluster_variance(cov,left),1e-18); rv=max(_cluster_variance(cov,right),1e-18)
            alpha=rv/(lv+rv)
            weights.loc[left]*=alpha; weights.loc[right]*=(1.0-alpha)
            if len(left)>1: next_clusters.append(left)
            if len(right)>1: next_clusters.append(right)
        clusters=next_clusters
    weights=weights.reindex(cov.columns).fillna(0.0)
    weights=weights/max(float(weights.sum()),1e-18)*float(total_weight)
    return weights

__all__=["hierarchical_risk_parity_weights"]
