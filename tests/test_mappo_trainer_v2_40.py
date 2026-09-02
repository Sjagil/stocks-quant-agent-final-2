import numpy as np
import pytest


def test_mappo_shapes_and_training(tmp_path):
    torch = pytest.importorskip("torch")
    from stocks.learning.mappo_trainer_v2_40 import train_mappo_file_v240
    rng=np.random.default_rng(3); t,a,f,g=32,3,5,7
    p=tmp_path/"d.npz"
    np.savez(p,local_obs=rng.normal(size=(t,a,f)).astype("f4"),global_obs=rng.normal(size=(t,g)).astype("f4"),actions=rng.uniform(.05,.95,size=(t,a)).astype("f4"),rewards=rng.normal(0,.01,size=(t,a)).astype("f4"),eligible_mask=np.ones((t,a),dtype=bool))
    out=train_mappo_file_v240(p,tmp_path/"m.pt",{"minimum_samples":16,"updates_per_cycle":2,"seed":1})
    assert out["samples"]==32 and out["agents"]==3
    assert out["execution_authority"]=="NONE"
