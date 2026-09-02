import json
from pathlib import Path


def test_config_safety_invariants():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/"config/autonomous_continuous_learning_v2_40.json").read_text())
    assert cfg["execution_authority"]=="NONE"
    assert cfg["broker_submission_enabled"] is False
    assert cfg["automatic_live_promotion"] is False
    assert cfg["automatic_champion_promotion"] is False


def test_new_runtime_contains_no_broker_order_submission_calls():
    root=Path(__file__).resolve().parents[1]
    texts="\n".join(p.read_text(errors="ignore") for p in (root/"src/stocks/learning").glob("*.py"))
    for forbidden in ("placeOrder(", ".place_order(", "submit_order(", "broker.submit"):
        assert forbidden not in texts
