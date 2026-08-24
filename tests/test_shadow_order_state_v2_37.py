from stocks.shadow.ledger_v2_37 import ShadowLedgerV237
from stocks.shadow.order_state_v2_37 import reduce_order

def test_order_partial_then_filled(tmp_path):
    with ShadowLedgerV237(tmp_path/"x.db") as l:
        base=dict(aggregate_type="ORDER",aggregate_id="O")
        l.append(event_id="C",event_type="SHADOW_ORDER_CREATED",payload={"decision_id":"D","strategy_id":"S","family":"F","symbol":"AAA","side":"BUY","requested_notional":1000,"requested_quantity":10,"predicted_cost_bps":5},event_time="2026-08-24T00:00:00Z",**base)
        l.append(event_id="F1",event_type="SHADOW_FILL_RECORDED",payload={"quantity":4,"fill_price":100,"order_progress_notional":400,"explicit_cost_amount":1},event_time="2026-08-24T00:01:00Z",**base)
        assert reduce_order(l.events(aggregate_type="ORDER",aggregate_id="O")).status=="PARTIALLY_FILLED"
        l.append(event_id="F2",event_type="SHADOW_FILL_RECORDED",payload={"quantity":6,"fill_price":101,"order_progress_notional":600,"explicit_cost_amount":1},event_time="2026-08-24T00:02:00Z",**base)
        assert reduce_order(l.events(aggregate_type="ORDER",aggregate_id="O")).status=="FILLED"
