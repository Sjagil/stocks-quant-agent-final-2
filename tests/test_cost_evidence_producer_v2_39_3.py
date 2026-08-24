from pathlib import Path
import pandas as pd
from stocks.research.continuous.cost_evidence_producer_v2_39_3 import produce_cost_stress_from_oos


def _frame(n=80, gross=.004):
    base=pd.Timestamp('2025-01-01T00:00:00Z')
    return pd.DataFrame([{'gross_return':gross if i%5 else -.001} for i in range(n)])


def test_cost_stress_requires_explicit_2x_and_sample(tmp_path):
    r,rows=produce_cost_stress_from_oos(_frame(),entity_id='STRATEGY:h',base_cost_bps_per_side=3,effective_observations=80,minimum_effective_observations=60,output_dir=tmp_path,config={'multipliers':[1,1.5,2,3],'required_multiplier':2,'require_effective_sample_for_pass':True},provenance_hash='x')
    assert [x['stress_multiplier'] for x in rows]==[1.0,1.5,2.0,3.0]
    assert r.required_multiplier_passed is True
    assert r.max_positive_multiplier>=2
    assert all(x['execution_authority']=='NONE' for x in rows)
    assert all('v233_linear_expectancy_bps' in x for x in rows)
    assert all('v236_mean_edge_after_cost_bps' in x for x in rows)


def test_cost_stress_positive_returns_do_not_bypass_sample_gate(tmp_path):
    r,rows=produce_cost_stress_from_oos(_frame(20),entity_id='STRATEGY:h',base_cost_bps_per_side=3,effective_observations=20,minimum_effective_observations=60,output_dir=tmp_path,config={'multipliers':[1,2,3],'required_multiplier':2,'require_effective_sample_for_pass':True},provenance_hash='x')
    assert r.required_multiplier_passed is False
    assert 'INSUFFICIENT_EFFECTIVE_OOS_SAMPLE' in r.reasons
    assert all(not x['passed'] for x in rows)
