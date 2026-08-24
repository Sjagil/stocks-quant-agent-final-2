from types import SimpleNamespace
import pytest
from stocks.shadow.attribution_v2_37 import attribute_closed_position
from stocks.shadow.feedback_v2_37 import build_shadow_feedback

def test_attribution_and_feedback():
    p=SimpleNamespace(
        status="CLOSED",position_id="P",strategy_id="S",family="F",symbol="AAA",entry_notional=1000,
        realized_reference_gross_pnl=100,realized_fill_pnl=92,
        entry_explicit_cost_amount=2,exit_explicit_cost_amount=2,
        entry_implementation_shortfall_amount=5,exit_implementation_shortfall_amount=5,
        realized_net_pnl=88,mfe_bps=1500,mae_bps=-300,bars_held=10,exit_reason="TAKE_PROFIT")
    a=attribute_closed_position(p)
    f=build_shadow_feedback(a,forecast_gross_edge_bps=800,predicted_round_trip_cost_bps=80)
    assert a.net_return_bps==pytest.approx(880)
    assert a.implementation_shortfall_bps==pytest.approx(100)
    assert f.realized_cost_bps==pytest.approx(100)
    assert f.cost_prediction_error_bps==pytest.approx(20)
