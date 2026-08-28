from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.execution_simulator_v2_36 import simulate_execution

def test_bundle_research_only():
    result = simulate_execution(
        OrderIntentV236("A", 10_000),
        MarketStateV236("A", 10, 10, 20_000_000, .02),
        gross_edge_bps=150,
    )
    assert result.execution_authority == "NONE"
    assert len(result.cost_multiple_stress) == 4
    assert len(result.market_state_stress) == 5
