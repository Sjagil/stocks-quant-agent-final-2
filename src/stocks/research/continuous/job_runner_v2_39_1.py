from __future__ import annotations
import os,subprocess,sys
from pathlib import Path
from .health_v2_39_1 import assess_entity_hardened
from .scheduler_v2_39 import next_due
from .store_v2_39 import ResearchStoreV239

def _run_discovery(project_root:Path,payload:dict):
    script=(project_root/'scripts/run_parallel_research.py').resolve()
    if not script.is_file():return 2,'',f'missing allowlisted script: {script}'
    cmd=[sys.executable,str(script),'--limit',str(int(payload.get('limit',150)))]
    if payload.get('as_of'):cmd += ['--as-of',str(payload['as_of'])]
    c=subprocess.run(cmd,cwd=project_root,capture_output=True,text=True,check=False,env=os.environ.copy())
    return c.returncode,c.stdout,c.stderr

def execute_jobs_hardened(project_root:Path,store:ResearchStoreV239,*,max_jobs:int,scheduler_policy:dict,health_policy:dict,bayesian:dict,quality_weights:dict,worker_id='local-v2391'):
    store.reset_stale_leases(); jobs=store.claim_ready(limit=max_jobs,worker_id=worker_id,lease_seconds=int(scheduler_policy.get('job_lease_seconds',900)));done=failed=0
    for job in jobs:
        aid=store.record_attempt_start(job);rc=0;out='';err=''
        try:
            if job['job_type']=='DISCOVERY_REFRESH':rc,out,err=_run_discovery(project_root,job['payload'])
            elif job['job_type']=='ENTITY_REVALIDATION':
                a=assess_entity_hardened(store,job['entity_id'],policy=health_policy,bayesian=bayesian,quality_weights=quality_weights)
                store.set_entity_health(job['entity_id'],a.health,next_due_at=next_due(store.get_entity(job['entity_id']),scheduler_policy));store.add_recommendation(job['entity_id'],a.recommendation,a.score,a.reasons);out=str(a.as_dict())
            else:rc=2;err=f'job type not allowlisted: {job["job_type"]}'
        except Exception as exc:rc=1;err=f'{type(exc).__name__}: {exc}'
        ok=rc==0;store.finish_job(job,success=ok,attempt_id=aid,returncode=rc,stdout=out,stderr=err,retry_base_seconds=int(scheduler_policy.get('retry_base_seconds',60)));done+=int(ok);failed+=int(not ok)
    return {'claimed':len(jobs),'succeeded':done,'failed':failed}

__all__=['execute_jobs_hardened']
