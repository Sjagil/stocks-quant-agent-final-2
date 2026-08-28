import numpy as np
import pandas as pd

from stocks.research.alpha_factory_v2_31 import AlphaFactoryV231
from stocks.research.feature_registry_v2_31 import FeatureFamily, FeatureRegistry, FeatureSpec
from stocks.research.regime_feature_value_v2_31 import current_regime_multiplier, regime_conditioned_feature_value


def _panel():
    rng=np.random.default_rng(231)
    rows=[]
    for date in range(20):
        regime="TREND" if date<10 else "CHOP"
        for i in range(25):
            f=rng.normal()
            noise=rng.normal()
            target=0.08*f+rng.normal(scale=0.04)
            rows.append({"date":date,"regime":regime,"f":f,"noise":noise,"target":target,"fwd2":0.05*f+rng.normal(scale=0.05)})
    return pd.DataFrame(rows)


def test_regime_shrinkage_and_factory_report():
    panel=_panel()
    values=regime_conditioned_feature_value(panel,feature_id="f",date_column="date",target_column="target",regime_column="regime",shrinkage_periods=20)
    assert len(values)==2
    assert 0 <= current_regime_multiplier(values,current_regime="TREND") <= 1
    registry=FeatureRegistry((FeatureSpec("f",FeatureFamily.CROSS_SECTIONAL,"synthetic",cross_sectional=True),FeatureSpec("noise",FeatureFamily.CROSS_SECTIONAL,"noise",cross_sectional=True)))
    result=AlphaFactoryV231(registry=registry).evaluate(panel,feature_ids=["f","noise"],date_column="date",primary_target="target",forward_targets={1:"target",2:"fwd2"})
    assert result.status=="READY"
    assert result.feature_count==2
    assert result.promoted_count>=1
    assert result.execution_authority=="NONE"
