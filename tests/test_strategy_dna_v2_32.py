from stocks.research.strategy_generation_v2_32 import generate_strategy_dna


def test_dna_ids_are_stable_unique_and_safe():
    a = generate_strategy_dna(maximum_variants_per_family=2, seed=7)
    b = generate_strategy_dna(maximum_variants_per_family=2, seed=7)
    assert [x.dna_id for x in a] == [x.dna_id for x in b]
    assert len({x.dna_id for x in a}) == len(a)
    assert all(x.execution_authority == "NONE" for x in a)
    assert all(not x.sizing.leverage_allowed for x in a)
    assert all(not x.research_compliance_gate_applied for x in a)
