from stocks.portfolio.exposure_overlap_v2_35 import weighted_holdings_overlap, holdings_cosine_similarity, effective_constituents

def test_weighted_overlap_and_effective_n():
    a={"A":0.5,"B":0.5}; b={"A":0.5,"C":0.5}
    assert abs(weighted_holdings_overlap(a,b)-0.5)<1e-12
    assert 0 < holdings_cosine_similarity(a,b) < 1
    assert abs(effective_constituents(a)-2.0)<1e-12
