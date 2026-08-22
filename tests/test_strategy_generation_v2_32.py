from stocks.research.strategy_generation_v2_32 import generate_strategy_dna, sample_parameter_variants
from stocks.research.strategy_family_registry_v2_32 import family_registry


def test_generation_is_deterministic_and_has_variants():
    rows = generate_strategy_dna(maximum_variants_per_family=3, seed=32)
    assert len(rows) >= 45
    assert len({x.family for x in rows}) >= 15
    template = family_registry()[0]
    variants = sample_parameter_variants(template, maximum=5, seed=32)
    assert variants[0] == template.default_parameters
    assert len(variants) == 5
