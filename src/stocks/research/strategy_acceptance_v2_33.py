from __future__ import annotations
from typing import Sequence
import numpy as np
from stocks.quant.portfolio_metrics import profit_factor, trade_expectancy
from .cost_stress_v2_33 import CostStressScenario
from .return_distribution_v2_33 import clean_returns, max_drawdown_from_returns
from .validation_contracts_v2_33 import StrategyValidationDecision, ValidationPolicyV233
from .validation_score_v2_33 import validation_quality_score


def decide_strategy_acceptance(
    *, strategy_id: str, period_returns, trade_returns, psr: float, pbo: float,
    walkforward_efficiency: float | None, parameter_robustness: float,
    cost_stress: Sequence[CostStressScenario], no_leakage: bool,
    cross_engine_validated: bool=False, policy: ValidationPolicyV233 | None=None,
) -> StrategyValidationDecision:
    cfg=policy or ValidationPolicyV233(); period=clean_returns(period_returns); trades=clean_returns(trade_returns)
    pf=float(profit_factor(trades)); exp=float(trade_expectancy(trades)); mdd=float(max_drawdown_from_returns(period))
    required=min(cost_stress,key=lambda x: abs(x.multiple-cfg.required_cost_stress_multiple)) if cost_stress else None
    blockers=[]
    if len(period)<cfg.min_observations: blockers.append("INSUFFICIENT_OBSERVATIONS")
    if len(trades)<cfg.min_trades: blockers.append("INSUFFICIENT_TRADES")
    if np.isnan(pf) or pf<cfg.min_profit_factor: blockers.append("PROFIT_FACTOR_TOO_LOW")
    if not np.isfinite(exp) or exp<=cfg.min_expectancy: blockers.append("EXPECTANCY_NOT_POSITIVE")
    if not np.isfinite(psr) or psr<cfg.min_psr: blockers.append("PSR_TOO_LOW")
    if not np.isfinite(pbo) or pbo>cfg.max_pbo: blockers.append("PBO_TOO_HIGH")
    if walkforward_efficiency is None or not np.isfinite(walkforward_efficiency) or walkforward_efficiency<cfg.min_walkforward_efficiency: blockers.append("WALKFORWARD_EFFICIENCY_LOW")
    if parameter_robustness<cfg.min_parameter_robustness: blockers.append("PARAMETER_ROBUSTNESS_LOW")
    if not np.isfinite(mdd) or mdd>cfg.max_drawdown: blockers.append("MAX_DRAWDOWN_TOO_HIGH")
    if cfg.require_cost_stress_positive and (required is None or not required.positive): blockers.append("COST_STRESS_FAILED")
    if cfg.require_no_leakage and not no_leakage: blockers.append("LEAKAGE_DETECTED")
    if cfg.require_cross_engine_validation and not cross_engine_validated: blockers.append("CROSS_ENGINE_REQUIRED")
    score=validation_quality_score(psr=psr,pbo=pbo,profit_factor=pf,expectancy=exp,wfe=walkforward_efficiency,parameter_robustness=parameter_robustness,max_drawdown=mdd,cost_stress_positive=bool(required and required.positive))
    return StrategyValidationDecision(
        strategy_id=strategy_id,status="PROMOTE_VALIDATION" if not blockers else "REJECT_OR_REWORK",blockers=tuple(blockers),score=score,
        metrics={"observations":len(period),"trades":len(trades),"profit_factor":pf,"expectancy":exp,"max_drawdown":mdd},
        statistical={"psr":float(psr),"pbo":float(pbo)},robustness={"walkforward_efficiency":walkforward_efficiency,"parameter_robustness":float(parameter_robustness)},
        cost_stress={"required_multiple":cfg.required_cost_stress_multiple,"passed":bool(required and required.positive),"scenarios":[x.as_dict() for x in cost_stress]},
        no_leakage=bool(no_leakage),cross_engine_validated=bool(cross_engine_validated),
    )


__all__=["decide_strategy_acceptance"]
