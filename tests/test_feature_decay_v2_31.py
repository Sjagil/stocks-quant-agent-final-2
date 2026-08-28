import numpy as np
import pandas as pd

from stocks.research.feature_decay_v2_31 import cross_sectional_ic_decay_curve, decay_half_life_from_curve


def test_cross_sectional_decay_curve_uses_forward_horizons():
    rng=np.random.default_rng(99)
    rows=[]
    for d in range(12):
        x=rng.normal(size=20)
        for i,v in enumerate(x):
            rows.append({"date":d,"f":v,"r1":v+rng.normal(scale=.2),"r2":.5*v+rng.normal(scale=.4)})
    panel=pd.DataFrame(rows)
    curve=cross_sectional_ic_decay_curve(panel,feature_id="f",date_column="date",forward_targets={1:"r1",2:"r2"})
    assert curve["horizon_bars"].tolist()==[1,2]
    assert curve.loc[0,"mean_rank_ic"] > curve.loc[1,"mean_rank_ic"]
    value=decay_half_life_from_curve(curve)
    assert value is not None and value > 0
