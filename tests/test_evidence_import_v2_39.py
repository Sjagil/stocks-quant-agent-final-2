from stocks.research.continuous.evidence_v2_39 import ingest_evidence_records
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_generic_evidence_can_register_new_model(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); out=ingest_evidence_records(s,[{'entity_id':'RL:ppo1','entity_type':'RL_POLICY','evidence_type':'OOS','as_of':'2026-08-25T00:00:00+00:00','source':'v2.38','source_ref':'eval1','metrics':{'net_return':.1,'sharpe':1.2,'quality_score':.8}}])
 assert out['added']==1 and s.get_entity('RL:ppo1')['entity_type']=='RL_POLICY'
