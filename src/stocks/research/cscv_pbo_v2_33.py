from __future__ import annotations
import itertools, math
from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class PBOResult:
    pbo: float
    split_count: int
    median_logit: float
    median_oos_rank: float
    probability_of_loss: float
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)


def _sharpe(x: np.ndarray) -> float:
    x=x[np.isfinite(x)]
    if len(x)<2: return -float("inf")
    s=float(np.std(x,ddof=1))
    return -float("inf") if s<=1e-15 else float(np.mean(x)/s)


def combinatorially_symmetric_pbo(returns_matrix, *, slices: int = 8) -> PBOResult:
    m=np.asarray(returns_matrix,dtype=float)
    if m.ndim!=2 or m.shape[1]<2: raise ValueError("returns_matrix must be T x N with N>=2")
    if slices<4 or slices%2: raise ValueError("slices must be even and >=4")
    usable=(m.shape[0]//slices)*slices
    if usable<slices: raise ValueError("insufficient observations")
    m=m[:usable]; blocks=np.array_split(np.arange(usable),slices); half=slices//2
    logits=[]; ranks=[]; losses=[]
    all_blocks=set(range(slices))
    for combo in itertools.combinations(range(slices),half):
        is_blocks=set(combo); oos_blocks=all_blocks-is_blocks
        is_idx=np.concatenate([blocks[i] for i in sorted(is_blocks)])
        oos_idx=np.concatenate([blocks[i] for i in sorted(oos_blocks)])
        is_scores=np.array([_sharpe(m[is_idx,j]) for j in range(m.shape[1])])
        best=int(np.nanargmax(is_scores))
        oos_scores=np.array([_sharpe(m[oos_idx,j]) for j in range(m.shape[1])])
        order=np.argsort(oos_scores)
        position=int(np.where(order==best)[0][0])+1
        w=position/(m.shape[1]+1.0)
        w=float(np.clip(w,1e-12,1-1e-12))
        logits.append(math.log(w/(1-w))); ranks.append(w)
        losses.append(float(np.nanmean(m[oos_idx,best])) < 0.0)
    arr=np.asarray(logits)
    return PBOResult(
        pbo=float(np.mean(arr<=0.0)), split_count=len(arr), median_logit=float(np.median(arr)),
        median_oos_rank=float(np.median(ranks)), probability_of_loss=float(np.mean(losses)),
    )


__all__=["PBOResult","combinatorially_symmetric_pbo"]
