import numpy as np
from stocks.research.cscv_pbo_v2_33 import combinatorially_symmetric_pbo

def test_pbo_returns_valid_probability():
 rng=np.random.default_rng(3); m=rng.normal(0,0.01,(160,8)); result=combinatorially_symmetric_pbo(m,slices=8)
 assert 0<=result.pbo<=1 and result.split_count==70 and 0<result.median_oos_rank<1
