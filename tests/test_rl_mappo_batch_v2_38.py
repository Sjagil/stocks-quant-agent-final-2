import numpy as np
from stocks.rl.mappo_control_v2_38 import build_mappo_control_batch
def test_mappo_batch_masks_ineligible():
 b=build_mappo_control_batch(np.ones((3,2,4)),np.ones((3,5)),np.array([[1,0],[1,1],[0,1]],bool),np.ones(3),np.ones((3,2)),np.zeros((3,2))); assert b.rewards[0,1]==0; assert b.execution_authority=="NONE"
