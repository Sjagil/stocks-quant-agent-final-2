from stocks.research.feature_registry_v2_31 import default_feature_registry
from stocks.research.strategy_feasibility_v2_32 import evaluate_strategy_feasibility
from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def test_feasibility_requires_promoted_features():
    registry = default_feature_registry()
    dna = generate_strategy_dna(maximum_variants_per_family=1)[0]
    good = {x: {"status": "PROMOTE_RESEARCH"} for x in registry.ids()}
    assert evaluate_strategy_feasibility(dna, governance=good, registry=registry).status == "ELIGIBLE_RESEARCH"
    bad = dict(good); bad[dna.all_feature_ids[0]] = {"status": "REJECT_OR_REVIEW"}
    result = evaluate_strategy_feasibility(dna, governance=bad, registry=registry)
    assert result.status == "REJECTED_RESEARCH"
    assert "FEATURE_NOT_PROMOTED" in result.blockers
