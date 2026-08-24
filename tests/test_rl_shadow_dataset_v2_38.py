import pandas as pd, pytest
from stocks.rl.shadow_dataset_bridge_v2_38 import build_shadow_transition_dataset
def _frame(): return pd.DataFrame({"decision_time":["2026-01-01T00:00Z"],"outcome_time":["2026-01-02T00:00Z"],"symbol":["AAA"],"strategy_id":["S1"],"state_features":[{"x":1}],"action_weight":[.2],"realized_net_return":[.01],"realized_cost_bps":[10.]})
def test_shadow_dataset_causal(): assert build_shadow_transition_dataset(_frame()).causal is True
def test_shadow_dataset_rejects_future_leak_direction():
 f=_frame(); f.loc[0,"outcome_time"]="2025-12-31T00:00Z"
 with pytest.raises(AssertionError): build_shadow_transition_dataset(f)
