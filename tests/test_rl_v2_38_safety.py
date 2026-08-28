from pathlib import Path
import json
def test_v238_config_is_shadow_only():
 c=json.loads(Path("config/rl_portfolio_control_v2_38.json").read_text()); assert c["execution_authority"]=="NONE"; assert c["broker_submission_enabled"] is False; assert c["automatic_live_promotion"] is False; assert c["order_calls"]==0; assert c["research_compliance_gate_applied"] is False; assert c["promotion"]["challenger_only"] is True
