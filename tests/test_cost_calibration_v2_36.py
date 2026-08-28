from stocks.execution.cost_calibration_v2_36 import calibrate_cost_scale

def test_calibration_recovers_scale():
    result = calibrate_cost_scale([10] * 30, [15] * 30)
    assert result.status == "CALIBRATED"
    assert 1.49 < result.scale < 1.51
    assert result.mae_bps < 1e-9
