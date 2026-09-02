from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237
from stocks.shadow.reconciliation_v2_37 import reconcile_shadow_ledger

def test_reconciliation_ready(tmp_path):
    e=ShadowLifecycleEngineV237(tmp_path/"x.db")
    m=MarketStateV236("AAA",50,10,30_000_000,.02,liquidity_score=.9,data_quality_score=.95)
    d=ShadowDecisionV237("D","S","F","AAA",ShadowSide.BUY,10_000,180,"2026-08-24T10:00:00Z")
    sub=e.submit_entry(d,m); e.fill_entry(sub.order_id,m,fill_time="2026-08-24T10:01:00Z",force_fill_fraction=1)
    r=reconcile_shadow_ledger(e.ledger)
    assert r.status=="READY" and r.open_positions==1
    e.close()
