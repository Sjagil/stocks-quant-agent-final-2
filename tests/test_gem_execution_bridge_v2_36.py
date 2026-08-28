import pandas as pd
from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.research.gem_execution_bridge_v2_36 import apply_execution_economics_to_gems

def test_gem_bridge_adds_net_edge():
    gems = pd.DataFrame([
        {"symbol": "A", "gem_score": 80.0, "forecast_mean": .04},
        {"symbol": "B", "gem_score": 75.0, "forecast_mean": .0005},
    ])
    states = {
        "A": MarketStateV236("A", 10, 10, 50_000_000, .02),
        "B": MarketStateV236("B", 10, 80, 2_000_000, .05, liquidity_score=.5, data_quality_score=.9),
    }
    out = apply_execution_economics_to_gems(gems, states, research_notional=10_000)
    assert {"execution_cost_bps", "net_edge_bps", "execution_status", "execution_adjusted_gem_score"} <= set(out.columns)
    a = out[out.symbol == "A"].iloc[0]
    assert a.net_edge_bps > 0
