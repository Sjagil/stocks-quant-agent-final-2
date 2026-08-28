from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237

def test_bad_entry_edge_rejected_idempotently(tmp_path):
    e=ShadowLifecycleEngineV237(tmp_path/"x.db")
    m=MarketStateV236("AAA",50,80,1_100_000,.08,liquidity_score=.3,data_quality_score=.95)
    d=ShadowDecisionV237("D","S","F","AAA",ShadowSide.BUY,100_000,5,"2026-08-24T10:00:00Z")
    first=e.submit_entry(d,m)
    assert first.status=="REJECTED" and first.blockers
    second=e.submit_entry(d,m)
    assert second.status=="IDEMPOTENT_REJECTED"
    e.close()
