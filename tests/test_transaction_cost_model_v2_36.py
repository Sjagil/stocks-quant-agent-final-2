from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.transaction_cost_model_v2_36 import estimate_execution_cost

def state(spread=10, adv=20_000_000, vol=.02):
    return MarketStateV236("AAA", 50, spread, adv, vol, liquidity_score=.9, data_quality_score=.95)

def test_cost_positive_and_monotonic_size():
    s = state()
    small = estimate_execution_cost(OrderIntentV236("AAA", 10_000), s)
    big = estimate_execution_cost(OrderIntentV236("AAA", 200_000), s)
    assert small.total_cost_bps > 0
    assert big.total_cost_bps > small.total_cost_bps

def test_wider_spread_costs_more():
    a = estimate_execution_cost(OrderIntentV236("AAA", 20_000), state(5))
    b = estimate_execution_cost(OrderIntentV236("AAA", 20_000), state(50))
    assert b.total_cost_bps > a.total_cost_bps
