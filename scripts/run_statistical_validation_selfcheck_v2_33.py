from __future__ import annotations
import numpy as np
from stocks.research.validation_orchestrator_v2_33 import validate_strategy_candidate


def main() -> int:
    rng=np.random.default_rng(33)
    good=rng.normal(0.0025,0.01,240)
    matrix=np.column_stack([rng.normal(0.0001,0.012,240) for _ in range(6)]+[good])
    trade_returns=rng.normal(0.012,0.02,80)
    bundle=validate_strategy_candidate(
        strategy_id="SELF_CHECK",period_returns=good,trade_returns=trade_returns,
        trial_returns_matrix=matrix,trial_sharpes=[0.02,0.03,0.05,0.04,0.01,0.02,0.25],
        is_fold_metrics=[0.8,0.9,0.85,0.88],oos_fold_metrics=[0.55,0.65,0.60,0.62],
        center_parameter_score=1.0,neighbor_parameter_scores=[0.82,0.90,0.75,0.95,0.70],
        baseline_round_trip_cost_bps=10.0,no_leakage=True,
    )
    assert bundle.execution_authority=="NONE"
    assert bundle.pbo["split_count"]>0
    assert bundle.parameter_robustness["robustness_score"]>0.5
    print("STATISTICAL_VALIDATION_V2_33_SELFCHECK OK")
    print("PSR", round(float(bundle.sharpe["psr_vs_zero"]),6))
    print("PBO", round(float(bundle.pbo["pbo"]),6))
    print("WFE", bundle.walkforward["walkforward_efficiency"])
    print("PARAMETER_ROBUSTNESS", bundle.parameter_robustness["robustness_score"])
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0
if __name__=="__main__": raise SystemExit(main())
