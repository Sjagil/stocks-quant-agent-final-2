from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.idempotency_v2_37 import deterministic_identifier
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237
from stocks.shadow.position_state_v2_37 import reduce_position

def test_full_entry_partial_fill_and_forced_exit(tmp_path):
    e=ShadowLifecycleEngineV237(tmp_path/"x.db")
    m=MarketStateV236("AAA",50,10,30_000_000,.025,liquidity_score=.9,data_quality_score=.95)
    d=ShadowDecisionV237("D","S","F","AAA",ShadowSide.BUY,20_000,180,"2026-08-24T10:00:00Z")
    sub=e.submit_entry(d,m); assert sub.status=="ORDER_CREATED"
    assert e.submit_entry(d,m).status=="IDEMPOTENT_EXISTING"
    o=e.fill_entry(sub.order_id,m,fill_time="2026-08-24T10:01:00Z",force_fill_fraction=.5)
    assert o.status=="PARTIALLY_FILLED"
    o=e.fill_entry(sub.order_id,m,fill_time="2026-08-24T10:02:00Z",force_fill_fraction=1.0)
    assert o.status=="FILLED"
    pid=deterministic_identifier("POS",sub.order_id)
    x=MarketStateV236("AAA",53,10,30_000_000,.025,liquidity_score=.9,data_quality_score=.95)
    p=e.evaluate_and_exit(pid,x,bars_held=5,event_time="2026-08-24T12:00:00Z",force_exit=True)
    assert p.status=="CLOSED" and p.quantity==0
    e.close()
