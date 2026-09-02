from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.execution_style_compare_v2_36 import compare_execution_styles

def test_style_comparison_has_valid_choice():
    state = MarketStateV236("A", 10, 12, 50_000_000, .02, liquidity_score=.95, data_quality_score=.95)
    result = compare_execution_styles(OrderIntentV236("A", 20_000), state, gross_edge_bps=100)
    assert result.preferred_style in {"MARKET", "LIMIT"}
    assert result.limit_fill_probability > 0
