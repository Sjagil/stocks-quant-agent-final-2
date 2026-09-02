from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.scheduler_v2_39 import schedule_due_entity_reviews,schedule_discovery_if_due
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_scheduler_creates_deduplicated_due_jobs(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('S','STRATEGY'))
 pol={'candidate_revalidation_hours':24,'challenger_revalidation_hours':72,'champion_revalidation_hours':168,'watch_revalidation_hours':24,'degraded_revalidation_hours':12,'max_attempts':3,'discovery_refresh_hours':24}
 assert schedule_due_entity_reviews(s,pol)==1; schedule_due_entity_reviews(s,pol); assert len([j for j in s.jobs() if j['job_type']=='ENTITY_REVALIDATION'])==1
 assert schedule_discovery_if_due(s,pol,force=True) is True
