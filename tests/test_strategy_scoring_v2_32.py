from stocks.research.strategy_candidate_scoring_v2_32 import score_strategy_candidate
from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def test_candidate_score_is_bounded_and_research_only():
    dna = generate_strategy_dna(maximum_variants_per_family=1)[0]
    governance = {x: {"mean_rank_ic": 0.03, "rank_icir": 0.4, "stability_score": 0.7, "decay_half_life": dna.horizon.target_bars, "psi": 0.02} for x in dna.all_feature_ids}
    score = score_strategy_candidate(dna, governance)
    assert 0 <= score.score <= 1
    assert score.execution_authority == "NONE"
    assert score.research_only
