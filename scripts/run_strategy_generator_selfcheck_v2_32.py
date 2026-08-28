from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.research.feature_registry_v2_31 import default_feature_registry
from stocks.research.strategy_conditions_v2_32 import evaluate_strategy_panel
from stocks.research.strategy_generator_v2_32 import run_strategy_generator
from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def main() -> int:
    registry = default_feature_registry()
    governance = {
        feature_id: {
            "status": "PROMOTE_RESEARCH",
            "mean_rank_ic": 0.03,
            "rank_icir": 0.35,
            "stability_score": 0.70,
            "sign_consistency": 0.70,
            "decay_half_life": 30.0,
            "psi": 0.05,
        }
        for feature_id in registry.ids()
    }
    result = run_strategy_generator(
        governance,
        registry=registry,
        maximum_variants_per_family=3,
        maximum_selected=24,
        source_branch="SELF_CHECK",
        source_commit="SELF_CHECK",
    )
    assert result.generated_count >= 40
    assert result.feasible_count == result.generated_count
    assert result.selected_count >= 10
    assert result.family_count >= 8
    assert not result.research_compliance_gate_applied
    assert result.execution_authority == "NONE"
    dna = generate_strategy_dna(maximum_variants_per_family=1)[0]
    n = 50
    frame = pd.DataFrame({feature_id: np.linspace(-1.0, 2.0, n) for feature_id in dna.all_feature_ids})
    signals = evaluate_strategy_panel(frame, dna)
    assert list(signals.columns) == ["entry", "exit", "signal"]
    assert set(signals["signal"].unique()).issubset({-1, 0, 1})
    print("STRATEGY_GENERATOR_V2_32_SELFCHECK OK")
    print("GENERATED", result.generated_count)
    print("FEASIBLE", result.feasible_count)
    print("SELECTED", result.selected_count)
    print("FAMILIES", result.family_count)
    print("GENERIC_FEATURE_PANEL_EXECUTION", True)
    print("RESEARCH_COMPLIANCE_GATE_APPLIED", result.research_compliance_gate_applied)
    print("BROKER_SUBMISSION_ENABLED", result.broker_submission_enabled)
    print("ORDER_CALLS", result.order_calls)
    print("EXECUTION_AUTHORITY", result.execution_authority)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
