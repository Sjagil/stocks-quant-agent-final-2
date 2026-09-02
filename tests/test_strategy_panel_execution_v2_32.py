import numpy as np
import pandas as pd
from stocks.research.strategy_conditions_v2_32 import evaluate_strategy_panel
from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def test_generic_panel_execution_returns_signal_contract():
    dna = generate_strategy_dna(maximum_variants_per_family=1)[0]
    frame = pd.DataFrame({x: np.linspace(-2, 3, 100) for x in dna.all_feature_ids})
    out = evaluate_strategy_panel(frame, dna)
    assert out.index.equals(frame.index)
    assert set(out["signal"].unique()).issubset({-1, 0, 1})
    assert out["entry"].dtype == bool
