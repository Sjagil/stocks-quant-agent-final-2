import pandas as pd

from stocks.research.drift_v2_31 import jensen_shannon_divergence, population_stability_index
from stocks.research.pit_alignment_v2_31 import merge_asof_point_in_time


def test_drift_is_small_for_same_distribution_and_large_for_shift():
    ref=pd.Series(range(1000),dtype=float)
    same=ref.copy()
    shifted=ref+2000
    assert population_stability_index(ref,same) < 1e-9
    assert population_stability_index(ref,shifted) > 0.25
    assert jensen_shannon_divergence(ref,same) < 1e-9


def test_pit_join_never_uses_future_fact():
    decisions=pd.DataFrame({"symbol":["A","A"],"timestamp":["2026-01-02T12:00:00Z","2026-01-04T12:00:00Z"]})
    facts=pd.DataFrame({"symbol":["A","A"],"available_at":["2026-01-01T09:00:00Z","2026-01-03T09:00:00Z"],"eps":[1.0,2.0]})
    merged=merge_asof_point_in_time(decisions,facts)
    assert merged["eps"].tolist()==[1.0,2.0]
    assert (merged["available_at"] <= merged["timestamp"]).all()
