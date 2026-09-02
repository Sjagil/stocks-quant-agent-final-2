from stocks.production.state_store_v2_41 import ProductionStoreV241


def test_baseline_fill_ledger_and_idempotency(tmp_path):
    s = ProductionStoreV241(tmp_path / "prod.sqlite3")
    s.adopt_baseline({"AAPL": 2})
    payload = {"intent_id":"i1","symbol":"MSFT","action":"BUY","quantity":3,"source":"test"}
    assert s.claim_intent(payload) is True
    assert s.claim_intent(payload) is False
    fill = {"exec_id":"e1","broker_order_id":1,"intent_id":"i1","symbol":"MSFT","side":"BOT","shares":3,"price":100,"filled_at":"2026-01-01T00:00:00+00:00"}
    assert s.record_fill(fill) is True
    assert s.record_fill(fill) is False
    assert s.expected_positions() == {"AAPL":2.0,"MSFT":3.0}
    assert s.managed_symbols() == {"MSFT"}
    assert s.known_intent_ids() == {"i1"}
