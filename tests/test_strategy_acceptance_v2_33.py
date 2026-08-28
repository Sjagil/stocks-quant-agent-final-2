import numpy as np
from stocks.research.cost_stress_v2_33 import cost_stress_trade_returns
from stocks.research.strategy_acceptance_v2_33 import decide_strategy_acceptance

def test_acceptance_gates_are_hard_not_compensating():
 rng=np.random.default_rng(4); period=rng.normal(.002,.01,200); trades=rng.normal(.012,.02,60); costs=cost_stress_trade_returns(trades,baseline_round_trip_cost_bps=5)
 ok=decide_strategy_acceptance(strategy_id='x',period_returns=period,trade_returns=trades,psr=.99,pbo=.2,walkforward_efficiency=.8,parameter_robustness=.8,cost_stress=costs,no_leakage=True)
 assert ok.status=='PROMOTE_VALIDATION'
 bad=decide_strategy_acceptance(strategy_id='x',period_returns=period,trade_returns=trades,psr=.99,pbo=.2,walkforward_efficiency=.8,parameter_robustness=.8,cost_stress=costs,no_leakage=False)
 assert bad.status=='REJECT_OR_REWORK' and 'LEAKAGE_DETECTED' in bad.blockers
