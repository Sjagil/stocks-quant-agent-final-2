import pandas as pd
from stocks.rl.safe_controller_v2_38 import rl_action_to_shadow_target
def test_controller_requires_ready_reconciliation():
 x=rl_action_to_shadow_target(pd.Series([.2],index=["A"]),current_weights=pd.Series([0.],index=["A"]),accepted_mask=pd.Series([True],index=["A"]),reconciliation_status="BLOCKED"); assert x.status=="BLOCKED_RECONCILIATION" and x.weights=={}
def test_controller_emits_shadow_only():
 x=rl_action_to_shadow_target(pd.Series([.2],index=["A"]),current_weights=pd.Series([0.],index=["A"]),accepted_mask=pd.Series([True],index=["A"]),reconciliation_status="READY"); assert x.status=="SHADOW_TARGET_ONLY" and x.execution_authority=="NONE"
