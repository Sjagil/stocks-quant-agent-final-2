from __future__ import annotations
import json
from pathlib import Path
from .artifact_evidence_bridge_v2_39_1 import sync_known_artifact_evidence
from .candidate_sync_v2_39 import sync_candidate_registry
from .export_v2_39_1 import export_hardened_snapshot
from .health_v2_39_1 import assess_entity_hardened
from .job_runner_v2_39_1 import execute_jobs_hardened
from .scheduler_v2_39 import next_due,schedule_discovery_if_due,schedule_due_entity_reviews
from .shadow_ingest_v2_39 import ingest_shadow_inbox
from .store_v2_39 import ResearchStoreV239

def load_config_hardened(project_root:Path,config_path=None):
    path=Path(config_path) if config_path else project_root/'config/continuous_quant_research_v2_39_1.json'
    if not path.is_absolute():path=project_root/path
    cfg=json.loads(path.read_text())
    if cfg.get('execution_authority')!='NONE' or cfg.get('automatic_live_promotion') or cfg.get('automatic_champion_promotion') or cfg.get('broker_submission_enabled'):raise ValueError('v2.39.1 config attempted to escalate authority')
    return cfg

def runtime_paths_hardened(project_root:Path,cfg:dict):
    rr=project_root/cfg.get('runtime_root','artifacts/research_runtime/continuous_quant_research_v2_39');return rr,rr/cfg.get('database_name','research.db')

def recompute_all_hardened(store,cfg):
    n=0
    for e in store.list_entities(active_only=True):
        a=assess_entity_hardened(store,e['entity_id'],policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights']);due=e.get('next_due_at') or next_due(e,cfg['scheduler']);store.set_entity_health(e['entity_id'],a.health,next_due_at=due);store.add_recommendation(e['entity_id'],a.recommendation,a.score,a.reasons);n+=1
    return n

def run_research_cycle_hardened(project_root:Path,*,run_discovery=False,execute_ready=True,max_jobs=50,limit=None,as_of=None,config_path=None):
    cfg=load_config_hardened(project_root,config_path);rr,db=runtime_paths_hardened(project_root,cfg);store=ResearchStoreV239(db);cycle=store.begin_cycle();summary={'cycle_id':cycle,'schema':'continuous_quant_research_cycle_v2_39_1','run_discovery':bool(run_discovery)}
    try:
        if run_discovery:
            summary['discovery_scheduled']=schedule_discovery_if_due(store,cfg['scheduler'],force=True,limit=int(limit or cfg['discovery'].get('default_limit',150)),as_of=as_of);summary['discovery_jobs']=execute_jobs_hardened(project_root,store,max_jobs=1,scheduler_policy=cfg['scheduler'],health_policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights'])
        summary['candidate_sync']=sync_candidate_registry(project_root,store,rebuild=True)
        summary['artifact_evidence_sync']=sync_known_artifact_evidence(project_root,store) if cfg.get('artifact_evidence_bridge',{}).get('enabled',True) else {'disabled':True}
        summary['shadow_ingest']=ingest_shadow_inbox(project_root,store,list(cfg.get('inbox',{}).get('shadow_feedback_globs',[])))
        summary['health_recomputed']=recompute_all_hardened(store,cfg);summary['entity_reviews_scheduled']=schedule_due_entity_reviews(store,cfg['scheduler'])
        if execute_ready:summary['jobs']=execute_jobs_hardened(project_root,store,max_jobs=max_jobs,scheduler_policy=cfg['scheduler'],health_policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights'])
        summary['status']=export_hardened_snapshot(rr,store,cfg=cfg);store.finish_cycle(cycle,status='SUCCEEDED',summary=summary)
    except Exception as exc:summary['error']=f'{type(exc).__name__}: {exc}';store.finish_cycle(cycle,status='FAILED',summary=summary);raise
    (rr/'cycle_audit_v2_39_1.json').write_text(json.dumps(summary,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8');return summary

__all__=['load_config_hardened','runtime_paths_hardened','recompute_all_hardened','run_research_cycle_hardened']
