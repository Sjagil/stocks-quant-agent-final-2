import numpy as np
from stocks.research.block_bootstrap_v2_33 import moving_block_bootstrap,bootstrap_mean_ci

def test_block_bootstrap_shapes_and_ci():
 x=np.arange(40,dtype=float)/1000
 draws=moving_block_bootstrap(x,block_length=5,samples=100,seed=1)
 assert draws.shape==(100,40)
 lo,hi=bootstrap_mean_ci(x,block_length=5,samples=100,seed=1); assert lo<hi
