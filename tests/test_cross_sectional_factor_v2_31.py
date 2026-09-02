import numpy as np
import pandas as pd

from stocks.research.cross_sectional_factors_v2_31 import cross_sectional_momentum_panel
from stocks.research.factor_residuals_v2_31 import RollingFactorConfig, residual_momentum, rolling_factor_projection


def test_cross_sectional_momentum_and_sector_neutral_score():
    rows=[]
    for t in range(30):
        for i,s in enumerate(("A","B","C","D")):
            rows.append({"timestamp":t,"symbol":s,"sector":"X" if i<2 else "Y","close":100*(1+(i+1)*0.001)**t})
    out=cross_sectional_momentum_panel(pd.DataFrame(rows), window=10)
    tail=out[out.timestamp==29].set_index("symbol")
    assert tail.loc["D","cross_sectional_momentum_rank_10"] > tail.loc["A","cross_sectional_momentum_rank_10"]
    assert "sector_neutral_momentum_z_10" in out


def test_rolling_factor_projection_recovers_beta():
    n=120
    market=np.linspace(-0.01,0.01,n)
    noise=np.sin(np.arange(n))*0.0001
    asset=0.001+1.5*market+noise
    idx=pd.RangeIndex(n)
    out=rolling_factor_projection(pd.Series(asset,index=idx),pd.DataFrame({"market":market},index=idx),config=RollingFactorConfig(window=60,min_observations=40))
    assert abs(out["beta_market"].iloc[-1]-1.5) < 0.05
    assert out["idiosyncratic_vol"].iloc[-1] < 0.001
    mom=residual_momentum(out["factor_residual"].fillna(0.0),window=20)
    assert np.isfinite(mom.iloc[-1])
