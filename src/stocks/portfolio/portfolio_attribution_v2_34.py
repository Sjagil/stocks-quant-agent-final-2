from __future__ import annotations
from dataclasses import asdict, dataclass
import pandas as pd

@dataclass(frozen=True)
class PortfolioAttributionV234:
    gross_return: float; estimated_cost_drag: float; net_return: float; strategy_contribution: dict[str,float]; family_contribution: dict[str,float]; execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def attribute_period(weights: pd.Series, realized_returns: pd.Series, metadata: pd.DataFrame, *, turnover: float=0.0, estimated_cost_bps: float=0.0) -> PortfolioAttributionV234:
    idx=weights.index.union(realized_returns.index); w=pd.to_numeric(weights,errors="coerce").reindex(idx).fillna(0.0); r=pd.to_numeric(realized_returns,errors="coerce").reindex(idx).fillna(0.0); contrib=w*r; gross=float(contrib.sum()); drag=float(max(turnover,0.0)*max(estimated_cost_bps,0.0)/10000.0)
    meta=metadata.reindex(idx); fam={}
    if "family" in meta.columns:
        labels=meta["family"].fillna("UNKNOWN").astype(str)
        fam={str(x):float(contrib.loc[labels.index[labels==x]].sum()) for x in sorted(labels.unique())}
    return PortfolioAttributionV234(gross,drag,gross-drag,{k:float(v) for k,v in contrib.items()},fam)

__all__=["PortfolioAttributionV234","attribute_period"]
