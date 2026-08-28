import pandas as pd
from stocks.research.continuous.artifact_evidence_bridge_v2_39_1 import sync_known_artifact_evidence
from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.store_v2_39 import ResearchStoreV239
def test_artifact_bridge_does_not_fake_2x_cost_gate(tmp_path):
 p=tmp_path/'artifacts/research_runtime/strategy_generation_v2_22';p.mkdir(parents=True);pd.DataFrame([{'hypothesis_id':'h','median_test_expectancy_bps':10,'median_stress_test_expectancy_bps':4,'robustness_score':.8}]).to_csv(p/'validation_queue.csv',index=False);s=ResearchStoreV239(tmp_path/'r.db');s.upsert_entity(EntityV239('STRATEGY:h','STRATEGY'));out=sync_known_artifact_evidence(tmp_path,s);assert out['added']==2;cost=[e for e in s.evidence_for('STRATEGY:h') if e['evidence_type']=='COST_STRESS'][0];assert cost['metrics']['stress_multiplier']==1.0
