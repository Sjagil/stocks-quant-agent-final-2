from stocks.research.walkforward_diagnostics_v2_33 import walkforward_diagnostics

def test_walkforward_efficiency_and_stability():
 r=walkforward_diagnostics([1,1,1,1],[.7,.8,.6,.9])
 assert r.walkforward_efficiency==.75 and r.positive_oos_fraction==1.0 and r.stability_score>.5
