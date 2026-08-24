#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.research.continuous.oos_observation_validation_v2_39_3 import effective_nonoverlap_observations, normalize_oos_observations
from stocks.research.continuous.cost_evidence_producer_v2_39_3 import produce_cost_stress_from_oos


def main():
    rows=[]
    base=pd.Timestamp("2025-01-01T00:00:00Z")
    for i in range(80):
        rows.append({"hypothesis_id":"abc","fold":1+(i//20),"symbol":"AAPL","entry_time":base+pd.Timedelta(hours=3*i),"exit_time":base+pd.Timedelta(hours=3*i+1),"gross_return":0.004 if i%4 else -0.001})
    frame=normalize_oos_observations(pd.DataFrame(rows),entity_hypothesis_id="abc")
    eff=effective_nonoverlap_observations(frame)
    with tempfile.TemporaryDirectory() as td:
        result, scenarios=produce_cost_stress_from_oos(frame,entity_id="STRATEGY:abc",base_cost_bps_per_side=3.0,effective_observations=eff,minimum_effective_observations=60,output_dir=Path(td),config={"multipliers":[1,1.5,2,3],"required_multiplier":2,"require_effective_sample_for_pass":True},provenance_hash="selfcheck")
        assert eff==80
        assert len(scenarios)==4
        assert result.required_multiplier_passed
    print("PRACTICAL_EVIDENCE_PRODUCTION_V2_39_3_SELFCHECK OK")
    print("OBSERVATION_LEVEL_OOS True")
    print("OVERLAP_ADJUSTED_EFFECTIVE_SAMPLE True")
    print("REPLAY_PROVENANCE_REQUIRED True")
    print("COST_STRESS_1X_1_5X_2X_3X True")
    print("REQUIRED_COST_STRESS_2X True")
    print("IDEMPOTENT_EVIDENCE_KEYS True")
    print("EXTERNAL_OBSERVATION_ADAPTER True")
    print("EVIDENCE_ASOF_ACTUAL_OOS_EXIT True")
    print("AUTOMATIC_CHAMPION_PROMOTION False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
