import pandas as pd
from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.portfolio.rebalance_cost_projection_v2_36 import project_rebalance_costs

def test_post_cost_rebalance_gate():
    states = {
        "A": MarketStateV236("A", 10, 10, 50_000_000, .02),
        "B": MarketStateV236("B", 20, 12, 40_000_000, .025),
    }
    result = project_rebalance_costs(
        pd.Series({"A": .2}),
        pd.Series({"A": .1, "B": .1}),
        portfolio_value=100_000,
        market_states=states,
        pre_cost_utility_improvement=.01,
    )
    assert result.estimated_cost_amount > 0
    assert result.status == "REBALANCE_SHADOW_NET_POSITIVE"
