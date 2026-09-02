from stocks.research.cost_stress_v2_33 import cost_stress_trade_returns

def test_cost_stress_degrades_expectancy():
 rows=cost_stress_trade_returns([.01,-.004,.015,-.003,.012],baseline_round_trip_cost_bps=10)
 assert rows[0].expectancy>rows[-1].expectancy and [x.multiple for x in rows]==[1,1.5,2,3]
