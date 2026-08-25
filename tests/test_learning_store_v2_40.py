from pathlib import Path
from stocks.learning.contracts_v2_40 import AgentSpecV240
from stocks.learning.state_store_v2_40 import LearningStoreV240


def test_store_is_restart_safe(tmp_path: Path):
    path = tmp_path / "learning.sqlite3"
    spec = AgentSpecV240("ppo", "PPO", "SPY", "1h", "spy.parquet", timesteps_per_update=100)
    s = LearningStoreV240(path)
    s.upsert_agent(spec)
    run_id = s.begin_training("ppo", {"reason": "test"})
    s.finish_training(run_id, "ppo", status="SUCCEEDED", result={"data_rows": 1000, "latest_data_time": "2026-08-25T00:00:00+00:00", "model_path": "m.zip", "validation": {"sharpe": 1.0}, "test": {"sharpe": 0.8}})
    del s
    s2 = LearningStoreV240(path)
    row = s2.agent("ppo")
    assert row["state"] == "READY"
    assert row["last_data_rows"] == 1000
    assert row["latest_test"]["sharpe"] == 0.8
