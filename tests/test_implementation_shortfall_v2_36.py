from stocks.execution.cost_contracts_v2_36 import Side
from stocks.execution.implementation_shortfall_v2_36 import realized_implementation_shortfall

def test_buy_adverse_fill_positive_shortfall():
    result = realized_implementation_shortfall(
        decision_price=100, average_fill_price=100.2, filled_notional=10_000,
        explicit_cost_amount=5, side=Side.BUY,
    )
    assert result.total_shortfall_bps > 20
