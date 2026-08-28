from __future__ import annotations
import numpy as np
from .return_distribution_v2_33 import clean_returns


def moving_block_bootstrap(values, *, block_length: int = 10, samples: int = 1000, seed: int = 33) -> np.ndarray:
    x=clean_returns(values); n=len(x)
    if n<2 or block_length<1 or samples<10: raise ValueError("invalid bootstrap configuration")
    block=min(block_length,n); rng=np.random.default_rng(seed); out=np.empty((samples,n),dtype=float)
    starts=np.arange(0,n-block+1)
    for s in range(samples):
        pieces=[]
        while sum(len(p) for p in pieces)<n:
            start=int(rng.choice(starts)); pieces.append(x[start:start+block])
        out[s]=np.concatenate(pieces)[:n]
    return out


def bootstrap_mean_ci(values, *, confidence: float = 0.95, block_length: int = 10, samples: int = 1000, seed: int = 33) -> tuple[float,float]:
    draws=moving_block_bootstrap(values,block_length=block_length,samples=samples,seed=seed)
    means=draws.mean(axis=1); alpha=(1-confidence)/2
    return float(np.quantile(means,alpha)), float(np.quantile(means,1-alpha))


__all__=["bootstrap_mean_ci","moving_block_bootstrap"]
