import numpy as np
import pandas as pd

from stocks.research.feature_governance_v2_31 import (
    FeatureGovernancePolicy,
    correlation_clusters,
    estimate_ic_half_life,
    evaluate_feature_governance,
    variance_inflation_factors,
)


def _panel():
    rng=np.random.default_rng(31)
    rows=[]
    for date in range(24):
        x=rng.normal(size=30)
        y=0.08*x+rng.normal(scale=0.03,size=30)
        for i in range(30):
            rows.append({"date":date,"f":x[i],"noise":rng.normal(),"target":y[i]})
    return pd.DataFrame(rows)


def test_governance_promotes_predictive_feature():
    panel=_panel()
    result=evaluate_feature_governance(panel,feature_id="f",date_column="date",target_column="target",all_features=panel[["f","noise"]],ic_decay={1:0.4,2:0.25,4:0.12},policy=FeatureGovernancePolicy())
    assert result.status == "PROMOTE_RESEARCH"
    assert result.mean_rank_ic > 0
    assert result.decay_half_life is not None


def test_redundancy_clusters_and_vif_detect_duplicate():
    x=np.linspace(-1,1,100)
    frame=pd.DataFrame({"a":x,"b":x*1.001,"c":np.sin(np.arange(100))})
    clusters=correlation_clusters(frame,threshold=0.95)
    assert any(set(cluster)=={"a","b"} for cluster in clusters)
    vif=variance_inflation_factors(frame)
    assert vif["a"] > 20


def test_ic_half_life_exponential_curve():
    value=estimate_ic_half_life({1:0.4,2:0.2,3:0.1})
    assert value is not None and 0.9 < value < 1.1
