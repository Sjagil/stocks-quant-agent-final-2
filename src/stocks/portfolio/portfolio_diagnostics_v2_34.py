from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from stocks.quant.covariance import portfolio_volatility, risk_contribution, diversification_ratio, effective_number_of_positions
from stocks.quant.tail_risk import historical_var, expected_shortfall
from stocks.quant.portfolio_metrics import one_way_turnover
from .strategy_risk_budget_v2_34 import portfolio_heat

@dataclass(frozen=True)
class PortfolioDiagnosticsV234:
    expected_return: float; variance: float; volatility: float; var_95: float; expected_shortfall_95: float
    turnover: float; hhi: float; effective_positions: float; diversification_ratio: float; max_risk_contribution: float
    heat: float; family_exposure: dict[str,float]; cluster_exposure: dict[str,float]; risk_contributions: dict[str,float]
    execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def portfolio_diagnostics(weights: pd.Series, expected_returns: pd.Series, scenario_returns: pd.DataFrame, covariance: pd.DataFrame, metadata: pd.DataFrame, *, previous_weights: pd.Series|None=None) -> PortfolioDiagnosticsV234:
    cols=covariance.columns; w=pd.to_numeric(weights,errors="coerce").reindex(cols).fillna(0.0).clip(lower=0.0)
    mu=pd.to_numeric(expected_returns,errors="coerce").reindex(cols).fillna(0.0)
    scenarios=scenario_returns.reindex(columns=cols).dropna(how="any"); pr=scenarios.to_numpy(float)@w.to_numpy(float)
    vol=float(portfolio_volatility(w,covariance)); var=vol*vol; rc=risk_contribution(w,covariance)
    norm=w/max(float(w.sum()),1e-18); hhi=float(np.square(norm).sum()) if w.sum()>0 else 0.0
    prev=pd.Series(0.0,index=cols) if previous_weights is None else pd.to_numeric(previous_weights,errors="coerce").reindex(cols).fillna(0.0)
    meta=metadata.reindex(cols)
    def exposures(col):
        if col not in meta.columns: return {}
        labels=meta[col].fillna("UNKNOWN").astype(str); return {str(x):float(w.loc[labels.index[labels==x]].sum()) for x in sorted(labels.unique())}
    stops=pd.to_numeric(meta.get("stop_loss_fraction",pd.Series(0.0,index=cols)),errors="coerce").reindex(cols).fillna(0.0)
    return PortfolioDiagnosticsV234(float(mu@w),var,vol,historical_var(pr,alpha=.95),expected_shortfall(pr,alpha=.95),float(one_way_turnover(prev,w)),hhi,float(effective_number_of_positions(w)),float(diversification_ratio(w,covariance)) if w.sum()>0 else 0.0,float(rc.max()) if len(rc) else 0.0,float(portfolio_heat(w,stops)),exposures("family"),exposures("cluster"),{k:float(v) for k,v in rc.items()})

__all__=["PortfolioDiagnosticsV234","portfolio_diagnostics"]
