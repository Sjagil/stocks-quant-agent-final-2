from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236, OrderStyle
from stocks.execution.partial_fill_v2_36 import simulate_partial_fills

def test_limit_partial_fill_distribution():
    state = MarketStateV236("A", 10, 20, 10_000_000, .03, liquidity_score=.8, data_quality_score=.9)
    result = simulate_partial_fills(
        OrderIntentV236("A", 50_000, order_style=OrderStyle.LIMIT),
        state,
        simulations=500,
        seed=1,
    )
    assert 0 < result.p10_fill_fraction <= result.p50_fill_fraction <= result.p90_fill_fraction <= 1
