from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.idempotency_v2_37 import deterministic_identifier
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237

def test_stop_exit_not_blocked_by_positive_edge_requirement(tmp_path):
    e=ShadowLifecycleEngineV237(tmp_path/"x.db")
    m=MarketStateV236("AAA",100,10,30_000_000,.02,liquidity_score=.9,data_quality_score=.95)
    d=ShadowDecisionV237("D","S","F","AAA",ShadowSide.BUY,10_000,180,"2026-08-24T10:00:00Z",stop_loss_pct=.03)
    sub=e.submit_entry(d,m); e.fill_entry(sub.order_id,m,fill_time="2026-08-24T10:01:00Z",force_fill_fraction=1)
    pid=deterministic_identifier("POS",sub.order_id)
    down=MarketStateV236("AAA",95,20,5_000_000,.05,liquidity_score=.5,data_quality_score=.95)
    p=e.evaluate_and_exit(pid,down,bars_held=2,event_time="2026-08-24T11:00:00Z")
    assert p.status=="CLOSED" and p.exit_reason=="STOP_LOSS"
    e.close()
