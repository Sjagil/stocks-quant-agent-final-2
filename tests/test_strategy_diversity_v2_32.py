from stocks.research.strategy_diversity_v2_32 import select_diverse_candidates, strategy_similarity
from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def test_diversity_enforces_family_cap():
    rows = generate_strategy_dna(maximum_variants_per_family=4)
    selected = select_diverse_candidates(rows, maximum=20, max_per_family=1, max_similarity=1.0)
    assert len({x.family for x in selected}) == len(selected)
    assert all(0 <= strategy_similarity(selected[0], x) <= 1 for x in selected)
