import sqlite3
from stocks.shadow.ledger_v2_37 import ShadowLedgerV237

def test_hash_chain_detects_tampering(tmp_path):
    path=tmp_path/"x.db"
    with ShadowLedgerV237(path) as l:
        l.append(event_id="E1",aggregate_type="X",aggregate_id="A",event_type="T",payload={"x":1},event_time="2026-08-24T00:00:00Z")
    with sqlite3.connect(path) as c:
        c.execute("UPDATE shadow_events SET payload_json='{\"x\":2}' WHERE event_id='E1'"); c.commit()
    with ShadowLedgerV237(path) as l:
        assert not l.verify_hash_chain()
