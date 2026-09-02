from __future__ import annotations
from dataclasses import asdict, dataclass
import numpy as np
from stocks.quant.portfolio_metrics import sharpe_ratio
from .cost_stress_v2_33 import cost_stress_trade_returns
from .cscv_pbo_v2_33 import combinatorially_symmetric_pbo
from .parameter_robustness_v2_33 import parameter_neighborhood_robustness
from .multiple_testing_v2_33 import benjamini_hochberg, bonferroni, effective_independent_trials, holm
from .sharpe_significance_v2_33 import deflated_sharpe_probability, sample_sharpe_statistics
from .strategy_acceptance_v2_33 import decide_strategy_acceptance
from .validation_contracts_v2_33 import ValidationPolicyV233
from .walkforward_diagnostics_v2_33 import walkforward_diagnostics


@dataclass(frozen=True)
class ValidationBundleV233:
    decision: dict[str, object]
    sharpe: dict[str, object]
    deflated_sharpe: dict[str, object]
    pbo: dict[str, object]
    walkforward: dict[str, object]
    parameter_robustness: dict[str, object]
    multiple_testing: dict[str, object]
    execution_authority: str = "NONE"
    def as_dict(self): return asdict(self)


def validate_strategy_candidate(
    *, strategy_id: str, period_returns, trade_returns, trial_returns_matrix,
    trial_sharpes, is_fold_metrics, oos_fold_metrics, center_parameter_score: float,
    neighbor_parameter_scores, baseline_round_trip_cost_bps: float,
    no_leakage: bool=True, cross_engine_validated: bool=False,
    policy: ValidationPolicyV233 | None=None, p_values=None, trial_correlation=None,
) -> ValidationBundleV233:
    sharpe=sample_sharpe_statistics(period_returns)
    dsr=deflated_sharpe_probability(period_returns,trial_sharpes)
    pbo=combinatorially_symmetric_pbo(trial_returns_matrix)
    wf=walkforward_diagnostics(is_fold_metrics,oos_fold_metrics)
    pr=parameter_neighborhood_robustness(center_parameter_score,neighbor_parameter_scores)
    costs=cost_stress_trade_returns(trade_returns,baseline_round_trip_cost_bps=baseline_round_trip_cost_bps)
    pvals = list(p_values or [])
    mt = {"tests": len(pvals)}
    if pvals:
        mt.update({"bonferroni": bonferroni(pvals).tolist(), "holm": holm(pvals).tolist(), "benjamini_hochberg": benjamini_hochberg(pvals).tolist()})
    if trial_correlation is not None:
        mt["effective_independent_trials"] = effective_independent_trials(trial_correlation)
    decision=decide_strategy_acceptance(
        strategy_id=strategy_id,period_returns=period_returns,trade_returns=trade_returns,
        psr=float(sharpe["psr_vs_zero"]),pbo=pbo.pbo,walkforward_efficiency=wf.walkforward_efficiency,
        parameter_robustness=pr.robustness_score,cost_stress=costs,no_leakage=no_leakage,
        cross_engine_validated=cross_engine_validated,policy=policy,
    )
    return ValidationBundleV233(decision.as_dict(),sharpe,dsr,pbo.as_dict(),wf.as_dict(),pr.as_dict(),mt)


__all__=["ValidationBundleV233","validate_strategy_candidate"]
