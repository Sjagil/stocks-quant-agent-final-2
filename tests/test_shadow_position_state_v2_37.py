import pytest
from stocks.shadow.ledger_v2_37 import ShadowLedgerV237
from stocks.shadow.position_state_v2_37 import reduce_position

def test_position_tracks_mfe_mae_and_close(tmp_path):
    with ShadowLedgerV237(tmp_path/"x.db") as l:
        base=dict(aggregate_type="POSITION",aggregate_id="P")
        l.append(event_id="O",event_type="POSITION_OPENED",payload={
            "strategy_id":"S","family":"F","symbol":"AAA","quantity":10,
            "entry_price":101,"reference_price":100,
            "entry_explicit_cost_amount":1,"entry_implementation_shortfall_amount":11,
            "source_order_id":"O1"},event_time="2026-08-24T00:00:00Z",**base)
        l.append(event_id="M1",event_type="POSITION_MARK",payload={"price":111.1,"bars_held":5},event_time="2026-08-24T01:00:00Z",**base)
        l.append(event_id="M2",event_type="POSITION_MARK",payload={"price":95.95,"bars_held":6},event_time="2026-08-24T02:00:00Z",**base)
        l.append(event_id="C",event_type="POSITION_CLOSED",payload={
            "quantity":10,"exit_price":104,"reference_price":105,
            "exit_explicit_cost_amount":1,"exit_implementation_shortfall_amount":11,
            "reason":"TEST"},event_time="2026-08-24T03:00:00Z",**base)
        s=reduce_position(l.events(aggregate_type="POSITION",aggregate_id="P"))
        assert s.status=="CLOSED"
        assert s.mfe_bps==pytest.approx(1000)
        assert s.mae_bps==pytest.approx(-500)
        assert s.realized_reference_gross_pnl==pytest.approx(50)
        assert s.realized_fill_pnl==pytest.approx(30)
        assert s.realized_net_pnl==pytest.approx(28)
