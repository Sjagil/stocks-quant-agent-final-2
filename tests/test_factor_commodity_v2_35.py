import numpy as np, pandas as pd
from stocks.portfolio.factor_exposure_v2_35 import estimate_factor_betas, portfolio_factor_exposure
from stocks.portfolio.commodity_exposure_v2_35 import commodity_curve_metrics

def test_factor_beta_and_portfolio_exposure():
    rng=np.random.default_rng(2); m=rng.normal(0,0.01,100); q=rng.normal(0,0.01,100)
    y=1.2*m+0.3*q+rng.normal(0,0.001,100)
    beta=estimate_factor_betas(y,pd.DataFrame({"MARKET":m,"QUALITY":q}))
    assert abs(beta["MARKET"]-1.2)<0.08
    expo=portfolio_factor_exposure(pd.Series({"A":0.5,"B":0.5}),pd.DataFrame({"MARKET":[1.0,0.5]},index=["A","B"]))
    assert abs(expo["MARKET"]-0.75)<1e-12

def test_commodity_curve_backwardation():
    x=commodity_curve_metrics("oil",80,78,30,inventory_z=-1,trend_score=0.5)
    assert x.backwardation and x.annualized_roll_yield>0 and -1<=x.regime_score<=1
