import numpy as np,pandas as pd
from stocks.portfolio.strategy_covariance_v2_34 import strategy_covariance,correlation_from_covariance,effective_independent_strategies

def test_strategy_covariance_is_psd_and_effective_n_bounded():
 r=np.random.default_rng(1); x=pd.DataFrame(r.normal(size=(150,4))*0.01,columns=list('abcd')); cov=strategy_covariance(x); assert np.linalg.eigvalsh(cov.to_numpy()).min()>=-1e-10; n=effective_independent_strategies(correlation_from_covariance(cov)); assert 1<=n<=4.000001
