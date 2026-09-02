from stocks.research.strategy_generation_v2_32 import generate_strategy_dna
from stocks.research.strategy_handoff_v2_32 import VALIDATION_STAGES, build_research_handoff
from stocks.research.strategy_provenance_v2_32 import build_strategy_provenance


def test_provenance_and_handoff_freeze_and_block_live():
    dna = generate_strategy_dna(maximum_variants_per_family=1)[0]
    gov = {x: {"status": "PROMOTE_RESEARCH"} for x in dna.all_feature_ids}
    p = build_strategy_provenance(dna, governance=gov, generator_config={"x": 1}, source_branch="b", source_commit="c")
    h = build_research_handoff(dna, p, priority_score=0.5)
    assert p.parameters_frozen_for_handoff
    assert h.validation_stages == VALIDATION_STAGES
    assert not h.broker_submission_enabled
    assert not h.automatic_live_promotion
    assert h.order_calls == 0
    assert h.execution_authority == "NONE"
