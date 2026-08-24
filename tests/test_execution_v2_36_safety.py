import json
from pathlib import Path

def test_config_safety():
    cfg = json.loads(Path("config/execution_cost_liquidity_v2_36.json").read_text())
    assert cfg["research_compliance_gate_applied"] is False
    assert cfg["broker_submission_enabled"] is False
    assert cfg["automatic_live_promotion"] is False
    assert cfg["order_calls"] == 0
    assert cfg["execution_authority"] == "NONE"
