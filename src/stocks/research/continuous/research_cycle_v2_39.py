from __future__ import annotations
import json
from pathlib import Path
from .candidate_sync_v2_39 import sync_candidate_registry
from .export_v2_39 import export_snapshot
from .health_v2_39 import assess_entity
from .job_runner_v2_39 import execute_jobs
from .scheduler_v2_39 import next_due, schedule_discovery_if_due, schedule_due_entity_reviews
from .shadow_ingest_v2_39 import ingest_shadow_inbox
from .store_v2_39 import ResearchStoreV239

def load_config(project_root: Path, config_path: str|Path|None=None) -> dict:
    path=Path(config_path) if config_path else project_root/'config/continuous_quant_research_v2_39.json'
    if not path.is_absolute(): path=project_root/path
    cfg=json.loads(path.read_text())
    if cfg.get('execution_authority')!='NONE' or cfg.get('automatic_live_promotion') or cfg.get('automatic_champion_promotion') or cfg.get('broker_submission_enabled'):
        raise ValueError('v2.39 config attempted to escalate authority')
    return cfg

def runtime_paths(project_root: Path, cfg: dict):
    rr=project_root/cfg.get('runtime_root','artifacts/research_runtime/continuous_quant_research_v2_39')
    return rr, rr/cfg.get('database_name','research.db')

def recompute_all(store: ResearchStoreV239, cfg: dict) -> int:
    count=0
    for ent in store.list_entities(active_only=True):
        a=assess_entity(store,ent['entity_id'],policy=cfg['health'],bayesian=cfg['bayesian'])
        due=ent.get('next_due_at') or next_due(ent,cfg['scheduler'])
        store.set_entity_health(ent['entity_id'],a.health,next_due_at=due)
        store.add_recommendation(ent['entity_id'],a.recommendation,a.score,a.reasons); count+=1
    return count

def run_research_cycle(project_root: Path, *, run_discovery: bool=False, execute_ready: bool=True, max_jobs: int=50, limit: int|None=None, as_of: str|None=None, config_path=None) -> dict:
    cfg=load_config(project_root,config_path); runtime_root,db=runtime_paths(project_root,cfg); store=ResearchStoreV239(db); cycle=store.begin_cycle()
    summary={'cycle_id':cycle,'run_discovery':bool(run_discovery)}
    try:
        if run_discovery:
            summary['discovery_scheduled']=schedule_discovery_if_due(store,cfg['scheduler'],force=True,limit=int(limit or cfg['discovery'].get('default_limit',150)),as_of=as_of)
            summary['discovery_jobs']=execute_jobs(project_root,store,max_jobs=1,scheduler_policy=cfg['scheduler'],health_policy=cfg['health'],bayesian=cfg['bayesian'])
        summary['candidate_sync']=sync_candidate_registry(project_root,store,rebuild=True)
        summary['shadow_ingest']=ingest_shadow_inbox(project_root,store,list(cfg.get('inbox',{}).get('shadow_feedback_globs',[])))
        summary['health_recomputed']=recompute_all(store,cfg)
        summary['entity_reviews_scheduled']=schedule_due_entity_reviews(store,cfg['scheduler'])
        if execute_ready:
            summary['jobs']=execute_jobs(project_root,store,max_jobs=max_jobs,scheduler_policy=cfg['scheduler'],health_policy=cfg['health'],bayesian=cfg['bayesian'])
        summary['status']=export_snapshot(runtime_root,store)
        store.finish_cycle(cycle,status='SUCCEEDED',summary=summary)
    except Exception as exc:
        summary['error']=f'{type(exc).__name__}: {exc}'; store.finish_cycle(cycle,status='FAILED',summary=summary); raise
    (runtime_root/'cycle_audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    return summary

__all__=["load_config","recompute_all","run_research_cycle","runtime_paths"]
