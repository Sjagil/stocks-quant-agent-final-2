from stocks.shadow.ledger_v2_37 import ShadowLedgerV237

def test_ledger_append_idempotent_and_restart_hash_chain(tmp_path):
    path=tmp_path/"x.db"
    with ShadowLedgerV237(path) as l:
        assert l.append(event_id="E1",aggregate_type="X",aggregate_id="A",event_type="T",payload={"a":1},event_time="2026-08-24T00:00:00Z")
        assert not l.append(event_id="E1",aggregate_type="X",aggregate_id="A",event_type="T",payload={"a":1},event_time="2026-08-24T00:00:00Z")
        assert l.verify_hash_chain()
    with ShadowLedgerV237(path) as l:
        assert l.event_count()==1 and l.verify_hash_chain()
