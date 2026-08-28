from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237
from stocks.shadow.replay_v2_37 import replay_shadow_state

def test_restart_replay_identical(tmp_path):
    path=tmp_path/"x.db"
    e=ShadowLifecycleEngineV237(path)
    m=MarketStateV236("AAA",50,10,30_000_000,.02,liquidity_score=.9,data_quality_score=.95)
    d=ShadowDecisionV237("D","S","F","AAA",ShadowSide.BUY,10_000,180,"2026-08-24T10:00:00Z")
    sub=e.submit_entry(d,m); e.fill_entry(sub.order_id,m,fill_time="2026-08-24T10:01:00Z",force_fill_fraction=.5)
    a=replay_shadow_state(e.ledger).as_dict(); e.close()
    e2=ShadowLifecycleEngineV237(path); b=replay_shadow_state(e2.ledger).as_dict(); e2.close()
    assert a==b
