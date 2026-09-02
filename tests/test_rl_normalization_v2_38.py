import numpy as np
from stocks.rl.normalization_v2_38 import fit_robust_scaler,transform_robust
def test_robust_scaler_finite():
 x=np.array([[1,2],[2,2],[100,2]],float); y=transform_robust(x,fit_robust_scaler(x)); assert np.isfinite(y).all(); assert abs(y).max()<=8
