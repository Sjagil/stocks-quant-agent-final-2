from stocks.portfolio.dynamic_risk_overlay_v2_34 import *
def test_stress_reduces_exposure_multiplier():
 calm=dynamic_risk_overlay(DynamicRiskStateV234()); stress=dynamic_risk_overlay(DynamicRiskStateV234(drawdown=.10,drawdown_velocity=.02,realized_volatility=.30,regime_confidence=.3,liquidity_score=.5,data_quality_score=.8,loss_guard_score=.5)); assert stress.exposure_multiplier<calm.exposure_multiplier<=1
