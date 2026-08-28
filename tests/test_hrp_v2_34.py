import numpy as np,pandas as pd
from stocks.portfolio.hierarchical_risk_parity_v2_34 import hierarchical_risk_parity_weights

def test_hrp_long_only_and_sums_to_total():
 cov=pd.DataFrame([[.04,.01,0],[.01,.09,.01],[0,.01,.16]],index=list('abc'),columns=list('abc')); w=hierarchical_risk_parity_weights(cov,total_weight=.75); assert (w>=0).all(); assert abs(w.sum()-.75)<1e-10
