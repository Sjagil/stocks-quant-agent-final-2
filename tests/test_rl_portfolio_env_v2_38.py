import importlib.util, numpy as np, pandas as pd, pytest

@pytest.mark.skipif(importlib.util.find_spec("gymnasium") is None, reason="gymnasium optional")
def test_env_charges_external_execution_costs():
 from stocks.rl.portfolio_env_v2_38 import ShadowPortfolioControlEnvV238
 idx=pd.date_range("2026-01-01",periods=5,freq="D"); f=pd.DataFrame({"x":range(5)},index=idx); r=pd.DataFrame({"S1":[0,.01,.01,.01,.01]},index=idx); c=pd.DataFrame({"S1":[100,100,100,100,100]},index=idx)
 env=ShadowPortfolioControlEnvV238(f,r,accepted_mask=pd.Series({"S1":True}),execution_cost_bps=c); env.reset(seed=1); _,_,_,_,info=env.step(np.array([.2],dtype=np.float32)); assert info["implementation_cost_rate"]>0; assert info["net_return"]<info["gross_return"]
