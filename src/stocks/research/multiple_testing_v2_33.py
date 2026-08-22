from __future__ import annotations
import numpy as np


def bonferroni(p_values) -> np.ndarray:
    p = np.asarray(list(p_values), dtype=float)
    return np.clip(p * max(len(p), 1), 0.0, 1.0)


def holm(p_values) -> np.ndarray:
    p = np.asarray(list(p_values), dtype=float); n=len(p)
    order=np.argsort(p); adjusted=np.empty(n, dtype=float); running=0.0
    for rank, idx in enumerate(order):
        value=(n-rank)*p[idx]; running=max(running,value); adjusted[idx]=min(1.0,running)
    return adjusted


def benjamini_hochberg(p_values) -> np.ndarray:
    p=np.asarray(list(p_values),dtype=float); n=len(p)
    order=np.argsort(p); adjusted=np.empty(n,dtype=float); running=1.0
    for reverse_rank in range(n-1,-1,-1):
        idx=order[reverse_rank]; rank=reverse_rank+1
        value=p[idx]*n/rank; running=min(running,value); adjusted[idx]=min(1.0,running)
    return adjusted


def effective_independent_trials(correlation_matrix) -> float:
    corr=np.asarray(correlation_matrix,dtype=float)
    if corr.ndim != 2 or corr.shape[0] != corr.shape[1]:
        raise ValueError("correlation matrix must be square")
    eig=np.linalg.eigvalsh(np.nan_to_num(corr, nan=0.0))
    eig=np.clip(eig,0.0,None)
    total=eig.sum()
    return 0.0 if total<=1e-15 else float((total*total)/np.sum(eig*eig))


__all__=["benjamini_hochberg","bonferroni","effective_independent_trials","holm"]
