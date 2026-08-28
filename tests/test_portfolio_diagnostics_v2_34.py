import numpy as np,pandas as pd
from stocks.portfolio.portfolio_diagnostics_v2_34 import portfolio_diagnostics

def test_risk_contributions_sum_to_volatility():
 rng=np.random.default_rng(4); r=pd.DataFrame(rng.normal(0,.01,(100,2)),columns=['a','b']); cov=r.cov(); w=pd.Series({'a':.3,'b':.3}); meta=pd.DataFrame({'family':['f','g'],'cluster':['x','y'],'stop_loss_fraction':[.04,.05]},index=w.index); d=portfolio_diagnostics(w,r.mean(),r,cov,meta); assert abs(sum(d.risk_contributions.values())-d.volatility)<1e-9; assert d.heat>0
