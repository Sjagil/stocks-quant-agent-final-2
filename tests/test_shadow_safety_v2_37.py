import json
from pathlib import Path

def test_v237_config_and_source_safety():
    cfg=json.loads(Path("config/full_shadow_lifecycle_v2_37.json").read_text())
    assert cfg["broker_submission_enabled"] is False
    assert cfg["automatic_live_promotion"] is False
    assert cfg["order_calls"]==0
    assert cfg["execution_authority"]=="NONE"
    assert cfg["research_compliance_gate_applied"] is False
    assert cfg["lifecycle"]["long_only"] is True
    assert cfg["lifecycle"]["reconciliation_fail_closed"] is True
    root=Path("src/stocks/shadow")
    text="\n".join(p.read_text() for p in root.glob("*.py"))
    assert "placeOrder(" not in text
    assert "ib_insync" not in text
    assert "ibapi" not in text
