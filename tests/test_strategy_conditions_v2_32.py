import pandas as pd
from stocks.research.strategy_conditions_v2_32 import evaluate_condition
from stocks.research.strategy_dna_v2_32 import ConditionOperator, ConditionSpec


def test_cross_condition_is_causal():
    frame = pd.DataFrame({"x": [-1.0, 0.0, 1.0, 2.0]})
    cond = ConditionSpec("x", ConditionOperator.CROSS_ABOVE, value=0.5)
    out = evaluate_condition(frame, cond, {})
    assert out.tolist() == [False, False, True, False]
