from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from stocks.quant.portfolio_metrics import one_way_turnover

@dataclass(frozen=True)
class PortfolioConstraintPolicyV234:
    max_total_weight: float=0.75
    max_strategy_weight: float=0.25
    max_family_weight: float=0.35
    max_cluster_weight: float=0.35
    max_turnover: float=0.30
    min_cash_weight: float=0.10
    normal_max_heat: float=0.04
    hard_max_heat: float=0.06
    long_only: bool=True
    leverage_allowed: bool=False
    research_compliance_gate_applied: bool=False
    execution_authority: str="NONE"
    def __post_init__(self):
        if not (0 < self.max_total_weight <= 1-self.min_cash_weight+1e-12): raise ValueError("invalid total/cash cap")
        for name in ("max_strategy_weight","max_family_weight","max_cluster_weight"):
            v=float(getattr(self,name));
            if not 0 < v <= self.max_total_weight: raise ValueError(f"invalid {name}")
        if not 0 <= self.max_turnover <= 1: raise ValueError("invalid turnover cap")
        if not self.long_only or self.leverage_allowed: raise ValueError("v2.34 research portfolio is long-only/unlevered")
        if self.execution_authority!="NONE": raise ValueError("cannot grant execution authority")

@dataclass(frozen=True)
class PortfolioProjectionV234:
    weights: dict[str,float]
    total_weight: float
    cash_weight: float
    turnover: float
    exposure_multiplier: float
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def _group_scale(weights: pd.Series, metadata: pd.DataFrame, column: str, cap: float) -> pd.Series:
    if column not in metadata.columns: return weights
    out=weights.copy()
    labels=metadata[column].reindex(out.index).fillna("UNKNOWN").astype(str)
    for label in sorted(labels.unique()):
        members=labels.index[labels==label]
        total=float(out.loc[members].sum())
        if total>cap+1e-12: out.loc[members]*=cap/total
    return out

def _heat_scale(weights: pd.Series, metadata: pd.DataFrame, p: PortfolioConstraintPolicyV234) -> pd.Series:
    if "stop_loss_fraction" not in metadata.columns:
        return weights
    stops=pd.to_numeric(metadata["stop_loss_fraction"],errors="coerce").reindex(weights.index).fillna(0.0).clip(lower=0.0)
    heat=float((weights*stops).sum())
    if heat>p.normal_max_heat+1e-12 and heat>0:
        return weights*(p.normal_max_heat/heat)
    return weights

def _feasible_previous(previous: pd.Series, metadata: pd.DataFrame, p: PortfolioConstraintPolicyV234) -> pd.Series:
    x=pd.to_numeric(previous,errors="coerce").fillna(0.0).clip(lower=0.0,upper=p.max_strategy_weight)
    x=_group_scale(x,metadata,"family",p.max_family_weight); x=_group_scale(x,metadata,"cluster",p.max_cluster_weight); x=_heat_scale(x,metadata,p)
    if x.sum()>p.max_total_weight: x*=p.max_total_weight/float(x.sum())
    return x

def project_strategy_weights(raw_weights: pd.Series, metadata: pd.DataFrame, *, previous_weights: pd.Series|None=None, exposure_multiplier: float=1.0, policy: PortfolioConstraintPolicyV234|None=None) -> PortfolioProjectionV234:
    p=policy or PortfolioConstraintPolicyV234(); multiplier=float(np.clip(exposure_multiplier,0.0,1.0))
    idx=pd.Index(raw_weights.index.astype(str)); meta=metadata.reindex(idx)
    w=pd.to_numeric(raw_weights,errors="coerce").fillna(0.0); w.index=idx
    if (w < -1e-12).any(): raise ValueError("negative raw weights are not allowed")
    w=w.clip(lower=0.0,upper=p.max_strategy_weight)
    target=min(p.max_total_weight*multiplier,1.0-p.min_cash_weight)
    if w.sum()>target and w.sum()>0: w*=target/float(w.sum())
    for _ in range(5):
        before=w.copy(); w=_group_scale(w,meta,"family",p.max_family_weight); w=_group_scale(w,meta,"cluster",p.max_cluster_weight)
        if float((w-before).abs().sum())<1e-14: break
    if w.sum()>target and w.sum()>0: w*=target/float(w.sum())
    w=_heat_scale(w,meta,p)
    prev=pd.Series(0.0,index=idx,dtype=float) if previous_weights is None else _feasible_previous(pd.to_numeric(previous_weights,errors="coerce").reindex(idx).fillna(0.0),meta,p)
    turnover=float(one_way_turnover(prev,w))
    if turnover>p.max_turnover+1e-12 and turnover>0:
        lam=p.max_turnover/turnover; w=prev+lam*(w-prev); turnover=float(one_way_turnover(prev,w))
    total=float(w.sum()); cash=float(1.0-total)
    return PortfolioProjectionV234({k:float(v) for k,v in w.items() if v>1e-12},total,cash,turnover,multiplier)

def assert_projection_constraints(projection: PortfolioProjectionV234, metadata: pd.DataFrame, policy: PortfolioConstraintPolicyV234|None=None) -> None:
    p=policy or PortfolioConstraintPolicyV234(); w=pd.Series(projection.weights,dtype=float)
    assert (w>=-1e-12).all(); assert float(w.sum())<=p.max_total_weight+1e-10; assert projection.cash_weight>=p.min_cash_weight-1e-10
    if len(w): assert float(w.max())<=p.max_strategy_weight+1e-10
    m=metadata.reindex(w.index)
    for col,cap in (("family",p.max_family_weight),("cluster",p.max_cluster_weight)):
        if col in m.columns:
            labels=m[col].fillna("UNKNOWN");
            for label in labels.unique(): assert float(w.loc[labels.index[labels==label]].sum())<=cap+1e-10
    if "stop_loss_fraction" in m.columns and len(w):
        stops=pd.to_numeric(m["stop_loss_fraction"],errors="coerce").fillna(0.0).clip(lower=0.0)
        heat=float((w*stops.reindex(w.index).fillna(0.0)).sum())
        assert heat<=p.normal_max_heat+1e-10
        assert heat<=p.hard_max_heat+1e-10
    assert projection.turnover<=p.max_turnover+1e-10

__all__=["PortfolioConstraintPolicyV234","PortfolioProjectionV234","project_strategy_weights","assert_projection_constraints"]
