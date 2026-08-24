from stocks.research.continuous.contracts_v2_39 import EntityV239,EvidenceRecordV239
from stocks.research.continuous.health_v2_39 import assess_entity
from stocks.research.continuous.store_v2_39 import ResearchStoreV239,utc_now
POL={'stale_evidence_hours':999,'psi_watch':.1,'psi_quarantine':.25,'js_watch':.08,'js_quarantine':.2,'decay_watch':.35,'decay_quarantine':.7,'disagreement_watch':.45,'disagreement_quarantine':.75,'minimum_shadow_trades_for_promotion_review':3,'minimum_independent_evidence_sources':1,'minimum_posterior_net_edge_bps':0}
B={'prior_mean_bps':0,'prior_strength':2}

def test_positive_shadow_evidence_recommends_review(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY',role='CHALLENGER'))
 for i,x in enumerate([10,12,15,11]): s.add_evidence(EvidenceRecordV239('S','SHADOW_TRADE',utc_now(),{'realized_net_return_bps':x},'shadow',f'p{i}',1))
 a=assess_entity(s,'S',policy=POL,bayesian=B); assert a.health=='HEALTHY' and a.recommendation=='RECOMMEND_CHAMPION_REVIEW' and a.posterior_net_edge_bps>0

def test_negative_posterior_quarantines(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY'))
 for i,x in enumerate([-10,-12,-15,-11]): s.add_evidence(EvidenceRecordV239('S','SHADOW_TRADE',utc_now(),{'realized_net_return_bps':x},'shadow',f'p{i}',1))
 assert assess_entity(s,'S',policy=POL,bayesian=B).health=='QUARANTINED'
