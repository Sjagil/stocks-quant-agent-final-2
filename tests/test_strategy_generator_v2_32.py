from stocks.research.feature_registry_v2_31 import default_feature_registry
from stocks.research.strategy_generator_v2_32 import run_strategy_generator


def _gov():
    reg = default_feature_registry()
    return reg, {x: {"status": "PROMOTE_RESEARCH", "mean_rank_ic": 0.03, "rank_icir": 0.4, "stability_score": 0.7, "decay_half_life": 30.0, "psi": 0.03} for x in reg.ids()}


def test_full_generator_produces_diverse_handoffs():
    reg, governance = _gov()
    result = run_strategy_generator(governance, registry=reg, maximum_variants_per_family=3, maximum_selected=20, source_branch="test", source_commit="abc")
    assert result.generated_count >= 45
    assert result.feasible_count == result.generated_count
    assert result.selected_count >= 10
    assert result.family_count >= 8
    assert all(x["execution_authority"] == "NONE" for x in result.handoffs)
    assert not result.research_compliance_gate_applied
