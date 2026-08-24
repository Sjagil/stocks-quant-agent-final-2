from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.execution.liquidity_state_v2_36 import assess_liquidity

def test_capacity_blocks_large_order():
    state = MarketStateV236("A", 10, 20, 2_000_000, .03)
    result = assess_liquidity(200_000, state)
    assert "ADV_FRACTION_EXCEEDED" in result.blockers
    assert result.capacity_notional == 100_000
