from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def test_job_claim_success_and_dedupe(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); j1=s.enqueue('DISCOVERY_REFRESH',dedupe_key='x'); j2=s.enqueue('DISCOVERY_REFRESH',dedupe_key='x'); assert j1==j2
 jobs=s.claim_ready(limit=2,worker_id='w'); assert len(jobs)==1 and jobs[0]['attempts']==1
 a=s.record_attempt_start(jobs[0]); s.finish_job(jobs[0],success=True,attempt_id=a)
 assert s.jobs()[0]['status']=='SUCCEEDED'

def test_failed_job_requeues_then_deadletters(tmp_path):
 s=ResearchStoreV239(tmp_path/'r.db'); s.enqueue('X',max_attempts=1,dedupe_key='x')
 j=s.claim_ready(limit=1,worker_id='w')[0]; a=s.record_attempt_start(j); s.finish_job(j,success=False,attempt_id=a,stderr='bad')
 assert s.jobs()[0]['status']=='DEADLETTER'
