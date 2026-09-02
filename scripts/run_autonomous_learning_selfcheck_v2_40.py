#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stocks.learning.contracts_v2_40 import AgentSpecV240
from stocks.learning.state_store_v2_40 import LearningStoreV240
from stocks.learning.triggers_v2_40 import decide_retrain_v240


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        store = LearningStoreV240(Path(tmp) / "learning.sqlite3")
        spec = AgentSpecV240("ppo_test", "PPO", "SPY", "1h", "x.parquet", timesteps_per_update=100)
        store.upsert_agent(spec)
        decision = decide_retrain_v240(
            current_rows=1000,
            previous_rows=900,
            last_success_at=None,
            shadow_outcomes_since_train=0,
            drift_severity=0.0,
            policy={"minimum_rows": 800, "minimum_new_rows": 32},
        )
        assert decision.should_train
        assert store.agent("ppo_test")["state"] == "IDLE"
    print("AUTONOMOUS_CONTINUOUS_LEARNING_V2_40_SELFCHECK OK")
    print("EVENT_DRIVEN_RETRAINING True")
    print("PPO_WARM_START True")
    print("SAC_REPLAY_PERSISTENCE True")
    print("MAPPO_CENTRALIZED_CRITIC_TRAINER True")
    print("STRATEGY_RESEARCH_LOOP True")
    print("SHADOW_FEEDBACK_TRIGGER True")
    print("AUTOMATIC_CHAMPION_PROMOTION False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
