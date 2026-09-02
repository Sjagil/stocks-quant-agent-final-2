from stocks.production.reconciliation_v2_41 import reconcile, ingest_broker_fills
from stocks.production.state_store_v2_41 import ProductionStoreV241


def setup(tmp_path):
    s=ProductionStoreV241(tmp_path/'p.sqlite3')
    s.adopt_baseline({})
    assert s.claim_intent({"intent_id":"abc","symbol":"SPY","action":"BUY","quantity":1,"source":"x"})
    s.record_order(broker_order_id=10,intent_id="abc",role="ENTRY",status="Submitted",order_ref="SQA:abc",payload={})
    return s


def test_unknown_external_order_blocks(tmp_path):
    s=setup(tmp_path)
    r=reconcile(s,{},({"order_id":99,"order_ref":"manual","symbol":"SPY"},))
    assert not r['passed'] and 'UNKNOWN_OPEN_BROKER_ORDERS' in r['blockers']


def test_unknown_sqa_ref_also_blocks(tmp_path):
    s=setup(tmp_path)
    r=reconcile(s,{},({"order_id":99,"order_ref":"SQA:not-in-ledger","symbol":"SPY"},))
    assert not r['passed']


def test_known_intent_ref_is_reconcilable(tmp_path):
    s=setup(tmp_path)
    r=reconcile(s,{},({"order_id":99,"order_ref":"SQA:abc","symbol":"SPY"},))
    assert r['passed']


def test_fill_without_known_intent_never_becomes_managed(tmp_path):
    s=setup(tmp_path)
    added=ingest_broker_fills(s,({"exec_id":"e","broker_order_id":7,"order_ref":"SQA:unknown","symbol":"NVDA","side":"BOT","shares":1,"price":1,"filled_at":"2026-01-01T00:00:00+00:00"},))
    assert added == 1
    assert "NVDA" not in s.managed_symbols()
