from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.execution_simulator_v2_36 import simulate_execution

def test_market_state_stress_increases_cost():
    state = MarketStateV236("A", 10, 10, 20_000_000, .02, liquidity_score=.9)
    result = simulate_execution(OrderIntentV236("A", 50_000), state, gross_edge_bps=150)
    rows = {row["scenario"]: row for row in result.market_state_stress}
    assert rows["LIQUIDITY_SHOCK"]["round_trip_cost_bps"] > rows["BASE"]["round_trip_cost_bps"]
