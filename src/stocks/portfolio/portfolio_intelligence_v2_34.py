from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
import pandas as pd
from .strategy_covariance_v2_34 import clean_strategy_returns, strategy_covariance, correlation_from_covariance, effective_independent_strategies
from .hierarchical_risk_parity_v2_34 import hierarchical_risk_parity_weights
from .dynamic_risk_overlay_v2_34 import DynamicRiskStateV234, dynamic_risk_overlay
from .strategy_risk_budget_v2_34 import evidence_risk_budgets
from .portfolio_constraints_v2_34 import PortfolioConstraintPolicyV234, project_strategy_weights, assert_projection_constraints
from .portfolio_diagnostics_v2_34 import portfolio_diagnostics
from .portfolio_utility_v2_34 import PortfolioUtilityPolicyV234, portfolio_utility

@dataclass(frozen=True)
class PortfolioCandidateV234:
    method: str; weights: dict[str,float]; utility: float; diagnostics: dict[str,object]; status: str="READY"; execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class PortfolioIntelligenceResultV234:
    status: str; selected_method: str; selected_weights: dict[str,float]; candidates: tuple[PortfolioCandidateV234,...]; covariance_method: str; effective_independent_strategies: float; risk_overlay: dict[str,object]; cash_weight: float; challenger_errors: dict[str,str]; execution_authority: str="NONE"
    def as_dict(self): return asdict(self)

def _raw_edge_weights(mu: pd.Series, budgets: pd.Series, total: float) -> pd.Series:
    raw=(mu.clip(lower=0.0)+1e-12)*budgets
    if raw.sum()<=0: raw=budgets.copy()
    return raw/max(float(raw.sum()),1e-18)*total

def build_portfolio_intelligence(strategy_returns: pd.DataFrame, expected_returns: pd.Series, metadata: pd.DataFrame, *, validated_ids: tuple[str,...] | list[str], previous_weights: pd.Series|None=None, risk_state: DynamicRiskStateV234|None=None, covariance_method: str="ledoit_wolf", periods_per_year: float|None=None, constraints: PortfolioConstraintPolicyV234|None=None, utility_policy: PortfolioUtilityPolicyV234|None=None, include_convex: bool=True) -> PortfolioIntelligenceResultV234:
    p=constraints or PortfolioConstraintPolicyV234()
    approved=tuple(dict.fromkeys(str(x) for x in validated_ids if str(x).strip()))
    if not approved: raise ValueError("validated_ids from v2.33 are required")
    missing=[x for x in approved if x not in strategy_returns.columns]
    if missing: raise ValueError(f"validated strategy returns missing: {missing}")
    frame=clean_strategy_returns(strategy_returns.loc[:,approved],min_observations=20); cols=frame.columns
    mu=pd.to_numeric(expected_returns,errors="coerce").reindex(cols)
    if mu.isna().any(): raise ValueError("expected returns missing for one or more strategies")
    meta=metadata.reindex(cols)
    for required in ("family","cluster","validation_score","stability_score","liquidity_score","stop_loss_fraction"):
        if required not in meta.columns: raise ValueError(f"metadata missing column: {required}")
    cov=strategy_covariance(frame,method=covariance_method,periods_per_year=periods_per_year,min_observations=20)
    corr=correlation_from_covariance(cov); effective=effective_independent_strategies(corr)
    overlay=dynamic_risk_overlay(risk_state or DynamicRiskStateV234())
    budgets=evidence_risk_budgets(mu,validation_scores=meta["validation_score"],stability_scores=meta["stability_score"],liquidity_scores=meta["liquidity_score"])
    raw_candidates={"ROBUST_EDGE_WEIGHTED":_raw_edge_weights(mu,budgets,p.max_total_weight),"HRP":hierarchical_risk_parity_weights(cov,total_weight=p.max_total_weight)}
    challenger_errors: dict[str,str]={}
    if include_convex:
        try:
            from .optimizer_v2_28 import OptimizerConstraints, minimum_variance_weights, mean_cvar_weights, risk_budgeting_weights
            oc=OptimizerConstraints(max_total_weight=p.max_total_weight,max_position_weight=p.max_strategy_weight)
            calls={
                "MIN_VARIANCE":lambda: minimum_variance_weights(cov,constraints=oc),
                "MEAN_CVAR":lambda: mean_cvar_weights(mu,frame,previous_weights=previous_weights,turnover_penalty=0.05 if previous_weights is not None else 0.0,constraints=oc),
                "RISK_BUDGETING":lambda: risk_budgeting_weights(cov,risk_budgets=budgets,constraints=oc),
            }
            for name,call in calls.items():
                try:
                    result=call()
                    if result.weights: raw_candidates[name]=pd.Series(result.weights,dtype=float).reindex(cols).fillna(0.0)
                    else: challenger_errors[name]=f"NO_WEIGHTS:{result.status}"
                except Exception as exc:
                    challenger_errors[name]=f"{type(exc).__name__}:{exc}"
        except ImportError as exc:
            challenger_errors["CONVEX_STACK"]=f"ImportError:{exc}"
    candidates=[]
    prev=pd.Series(0.0,index=cols) if previous_weights is None else pd.to_numeric(previous_weights,errors="coerce").reindex(cols).fillna(0.0)
    for method,raw in raw_candidates.items():
        projection=project_strategy_weights(raw.reindex(cols).fillna(0.0),meta,previous_weights=prev,exposure_multiplier=overlay.exposure_multiplier,policy=p); assert_projection_constraints(projection,meta,p)
        w=pd.Series(projection.weights,dtype=float).reindex(cols).fillna(0.0); diag=portfolio_diagnostics(w,mu,frame,cov,meta,previous_weights=prev); util=portfolio_utility(diag,utility_policy)
        candidates.append(PortfolioCandidateV234(method,projection.weights,util.score,diag.as_dict()))
    candidates=sorted(candidates,key=lambda c:(-c.utility,c.method)); best=candidates[0] if candidates else None
    if best is None: return PortfolioIntelligenceResultV234("EMPTY","NONE",{},tuple(),covariance_method,effective,overlay.as_dict(),1.0,challenger_errors)
    cash=1.0-sum(best.weights.values())
    return PortfolioIntelligenceResultV234("RESEARCH_PORTFOLIO_READY",best.method,best.weights,tuple(candidates),covariance_method,effective,overlay.as_dict(),float(cash),challenger_errors)

__all__=["PortfolioCandidateV234","PortfolioIntelligenceResultV234","build_portfolio_intelligence"]
