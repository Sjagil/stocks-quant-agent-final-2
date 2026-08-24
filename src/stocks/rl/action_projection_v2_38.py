from __future__ import annotations
from collections import defaultdict
import numpy as np
import pandas as pd
from .control_contracts_v2_38 import PortfolioControlPolicyV238, ProjectedPortfolioActionV238

def _turnover(a: pd.Series,b: pd.Series)->float:
    idx=a.index.union(b.index)
    return 0.5*float((a.reindex(idx).fillna(0)-b.reindex(idx).fillna(0)).abs().sum())

def _cap_groups(w: pd.Series, labels: dict[str,str], cap: float) -> pd.Series:
    out=w.copy()
    groups=defaultdict(list)
    for s in out.index: groups[str(labels.get(str(s),"UNKNOWN"))].append(s)
    for members in groups.values():
        total=float(out.loc[members].sum())
        if total > cap + 1e-12 and total > 0:
            out.loc[members] *= cap/total
    return out

def project_portfolio_action(
    raw_weights: pd.Series,
    *,
    current_weights: pd.Series | None=None,
    accepted_mask: pd.Series | None=None,
    family: dict[str,str] | None=None,
    cluster: dict[str,str] | None=None,
    stop_distance: pd.Series | None=None,
    policy: PortfolioControlPolicyV238 | None=None,
) -> ProjectedPortfolioActionV238:
    cfg=policy or PortfolioControlPolicyV238()
    raw=pd.to_numeric(raw_weights,errors="coerce").replace([np.inf,-np.inf],np.nan).fillna(0.0).astype(float)
    if raw.index.has_duplicates: raise ValueError("strategy ids must be unique")
    w=raw.clip(lower=0.0)
    blockers=[]
    if accepted_mask is not None:
        mask=accepted_mask.reindex(w.index).fillna(False).astype(bool)
        if ((w>0)&(~mask)).any(): blockers.append("UNACCEPTED_STRATEGY_ACTION_ZEROED")
        w=w.where(mask,0.0)
    elif cfg.v233_acceptance_required:
        raise ValueError("accepted_mask required by v2.33 acceptance contract")
    fam=family or {}; clu=cluster or {}
    w=w.clip(upper=cfg.max_strategy_weight)
    w=_cap_groups(w,fam,cfg.max_family_weight)
    w=_cap_groups(w,clu,cfg.max_cluster_weight)
    gross=float(w.sum())
    if gross>cfg.max_total_exposure and gross>0: w*=cfg.max_total_exposure/gross
    current=(pd.Series(0.0,index=w.index) if current_weights is None else pd.to_numeric(current_weights,errors="coerce").reindex(w.index).fillna(0.0).clip(lower=0.0))
    to=_turnover(current,w)
    if to>cfg.max_one_way_turnover+1e-12:
        alpha=cfg.max_one_way_turnover/to
        w=current+alpha*(w-current)
        w=w.clip(lower=0.0,upper=cfg.max_strategy_weight)
        w=_cap_groups(w,fam,cfg.max_family_weight)
        w=_cap_groups(w,clu,cfg.max_cluster_weight)
        gross=float(w.sum())
        if gross>cfg.max_total_exposure and gross>0: w*=cfg.max_total_exposure/gross
    sd=(pd.Series(0.0,index=w.index) if stop_distance is None else pd.to_numeric(stop_distance,errors="coerce").reindex(w.index).fillna(0.0).clip(lower=0.0))
    heat=float((w*sd).sum())
    if heat>cfg.max_portfolio_heat+1e-12 and heat>0:
        w*=cfg.max_portfolio_heat/heat
    gross=float(w.sum()); to=_turnover(current,w); heat=float((w*sd).sum())
    cash=max(0.0,1.0-gross)
    hard=[]
    if gross>cfg.max_total_exposure+1e-9: hard.append("TOTAL_EXPOSURE_EXCEEDED")
    if float(w.max())>cfg.max_strategy_weight+1e-9: hard.append("STRATEGY_CAP_EXCEEDED")
    if to>cfg.max_one_way_turnover+1e-9: hard.append("TURNOVER_CAP_EXCEEDED")
    if heat>cfg.max_portfolio_heat+1e-9: hard.append("HEAT_CAP_EXCEEDED")
    for labels,cap,name in ((fam,cfg.max_family_weight,"FAMILY_CAP_EXCEEDED"),(clu,cfg.max_cluster_weight,"CLUSTER_CAP_EXCEEDED")):
        totals=defaultdict(float)
        for sid,val in w.items(): totals[str(labels.get(str(sid),"UNKNOWN"))]+=float(val)
        if totals and max(totals.values())>cap+1e-9: hard.append(name)
    if cash<cfg.minimum_cash-1e-9: hard.append("MINIMUM_CASH_VIOLATED")
    if hard: raise AssertionError(f"projection failed closed: {hard}")
    projection=not np.allclose(w.to_numpy(),raw.reindex(w.index).fillna(0).to_numpy(),atol=1e-12)
    return ProjectedPortfolioActionV238({str(k):float(v) for k,v in w.items()},cash,gross,to,heat,tuple(blockers),projection)

__all__=["project_portfolio_action"]
