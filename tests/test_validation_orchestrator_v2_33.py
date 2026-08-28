import numpy as np
from stocks.research.validation_orchestrator_v2_33 import validate_strategy_candidate

def test_orchestrator_returns_complete_bundle():
 rng=np.random.default_rng(5); good=rng.normal(.002,.01,240); m=np.column_stack([rng.normal(0,.012,240) for _ in range(5)]+[good]); trades=rng.normal(.012,.02,70)
 b=validate_strategy_candidate(strategy_id='s',period_returns=good,trade_returns=trades,trial_returns_matrix=m,trial_sharpes=[0,.02,.03,.01,.04,.2],is_fold_metrics=[1,1,1,1],oos_fold_metrics=[.7,.8,.75,.72],center_parameter_score=1,neighbor_parameter_scores=[.8,.9,.75,.85],baseline_round_trip_cost_bps=5)
 assert b.execution_authority=='NONE' and 'decision' in b.as_dict() and b.pbo['split_count']>0 and 'multiple_testing' in b.as_dict()
