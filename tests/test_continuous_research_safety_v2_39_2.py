import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_config_stays_research_only():
    cfg = json.loads((ROOT / "config/continuous_quant_research_v2_39_2.json").read_text())
    assert cfg["execution_authority"] == "NONE"
    assert cfg["automatic_live_promotion"] is False
    assert cfg["automatic_champion_promotion"] is False
    assert cfg["broker_submission_enabled"] is False
    assert cfg["order_calls"] == 0
    assert cfg["research_compliance_gate_applied"] is False
    assert cfg["health"]["minimum_oos_observations"] >= 60
    assert cfg["health"]["minimum_cost_stress_multiplier"] >= 2.0


def test_v2392_code_has_no_broker_order_calls():
    root = ROOT / "src/stocks/research/continuous"
    text = "\n".join(p.read_text() for p in root.glob("*v2_39_2.py"))
    assert "placeOrder(" not in text
    assert 'EXECUTION_AUTHORITY = "LIVE"' not in text
