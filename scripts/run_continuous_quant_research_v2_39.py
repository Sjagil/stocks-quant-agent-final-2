#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path: sys.path.insert(0,str(ROOT/'src'))
from stocks.research.continuous.candidate_sync_v2_39 import sync_candidate_registry
from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.drift_ingest_v2_39 import compute_and_store_drift
from stocks.research.continuous.evidence_v2_39 import ingest_evidence_records, load_records
from stocks.research.continuous.export_v2_39 import export_snapshot
from stocks.research.continuous.health_v2_39 import assess_entity
from stocks.research.continuous.research_cycle_v2_39 import load_config, run_research_cycle, runtime_paths
from stocks.research.continuous.runtime_lock_v2_39 import exclusive_runtime_lock
from stocks.research.continuous.shadow_ingest_v2_39 import ingest_shadow_file
from stocks.research.continuous.store_v2_39 import ResearchStoreV239

def context(args):
    cfg=load_config(ROOT,args.config); rr,db=runtime_paths(ROOT,cfg); return cfg,rr,ResearchStoreV239(db)

def main():
    p=argparse.ArgumentParser(description='Continuous Quant Research Engine v2.39')
    p.add_argument('--config',default=None)
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init')
    cyc=sub.add_parser('cycle'); cyc.add_argument('--run-discovery',action='store_true'); cyc.add_argument('--max-jobs',type=int,default=50); cyc.add_argument('--limit',type=int,default=None); cyc.add_argument('--as-of',default=None); cyc.add_argument('--no-execute-ready',action='store_true')
    st=sub.add_parser('status')
    reg=sub.add_parser('register'); reg.add_argument('--entity-id',required=True); reg.add_argument('--entity-type',required=True); reg.add_argument('--family',default='UNKNOWN'); reg.add_argument('--source',default='MANUAL')
    ev=sub.add_parser('ingest-evidence'); ev.add_argument('--file',required=True)
    sh=sub.add_parser('ingest-shadow'); sh.add_argument('--file',required=True)
    dr=sub.add_parser('drift'); dr.add_argument('--entity-id',required=True); dr.add_argument('--reference',required=True); dr.add_argument('--current',required=True); dr.add_argument('--features',nargs='*')
    ap=sub.add_parser('approve-role'); ap.add_argument('--entity-id',required=True); ap.add_argument('--role',choices=['CANDIDATE','CHALLENGER','CHAMPION','RETIRED'],required=True); ap.add_argument('--reason',required=True)
    sub.add_parser('sync')
    ex=sub.add_parser('experiment'); ex.add_argument('--entity-id',default=None); ex.add_argument('--type',required=True); ex.add_argument('--hypothesis',required=True); ex.add_argument('--config-json',default='{}'); exr=sub.add_parser('experiment-result'); exr.add_argument('--experiment-id',required=True); exr.add_argument('--status',choices=['RUNNING','SUCCEEDED','FAILED','REJECTED'],required=True); exr.add_argument('--result-ref',default=None)
    sub.add_parser('doctor')
    wt=sub.add_parser('watch'); wt.add_argument('--interval-seconds',type=int,default=3600); wt.add_argument('--discovery-every',type=int,default=24); wt.add_argument('--max-jobs',type=int,default=50)
    args=p.parse_args(); cfg,rr,store=context(args)
    if args.cmd=='init': export_snapshot(rr,store); print('V2_39_INIT_OK',store.path); return 0
    if args.cmd=='cycle':
        result=run_research_cycle(ROOT,run_discovery=args.run_discovery,execute_ready=not args.no_execute_ready,max_jobs=args.max_jobs,limit=args.limit,as_of=args.as_of,config_path=args.config); print(json.dumps(result,indent=2,default=str)); return 0
    if args.cmd=='status':
        status=export_snapshot(rr,store); print(json.dumps(status,indent=2,default=str)); return 0
    if args.cmd=='register': store.register_manual(args.entity_id,args.entity_type,args.family,args.source); print('REGISTERED',args.entity_id); return 0
    if args.cmd=='ingest-evidence': print(json.dumps(ingest_evidence_records(store,load_records(args.file)),indent=2)); return 0
    if args.cmd=='ingest-shadow': print(json.dumps(ingest_shadow_file(store,args.file),indent=2)); return 0
    if args.cmd=='drift': print(json.dumps(compute_and_store_drift(store,args.entity_id,args.reference,args.current,features=args.features or None),indent=2)); return 0
    if args.cmd=='approve-role': store.set_role_manual(args.entity_id,args.role,args.reason); print('ROLE_SET',args.entity_id,args.role); return 0
    if args.cmd=='sync': print(json.dumps(sync_candidate_registry(ROOT,store,rebuild=True),indent=2,default=str)); return 0
    if args.cmd=='experiment':
        xid=store.register_experiment(entity_id=args.entity_id,experiment_type=args.type,hypothesis=args.hypothesis,config=json.loads(args.config_json)); print('EXPERIMENT_REGISTERED',xid); return 0
    if args.cmd=='experiment-result': store.update_experiment(args.experiment_id,status=args.status,result_ref=args.result_ref); print('EXPERIMENT_UPDATED',args.experiment_id,args.status); return 0
    if args.cmd=='doctor':
        checks={'db_exists':store.path.is_file(),'config_authority_none':cfg.get('execution_authority')=='NONE','automatic_live_promotion_false':not cfg.get('automatic_live_promotion'),'automatic_champion_promotion_false':not cfg.get('automatic_champion_promotion'),'broker_submission_false':not cfg.get('broker_submission_enabled'),'parallel_research_script':(ROOT/'scripts/run_parallel_research.py').is_file(),'candidate_registry_builder':(ROOT/'scripts/build_research_candidate_registry.py').is_file()}; checks['ready']=all(checks.values()); print(json.dumps(checks,indent=2)); return 0 if checks['ready'] else 2
    if args.cmd=='watch':
        if args.interval_seconds<60: raise SystemExit('watch interval must be >= 60 seconds')
        with exclusive_runtime_lock(rr/'research.lock'):
            print('V2_39_WATCH_RUNNING','interval',args.interval_seconds,'seconds')
            n=0
            while True:
                run_discovery=(n % max(1,int(args.discovery_every*3600/args.interval_seconds))==0)
                try: run_research_cycle(ROOT,run_discovery=run_discovery,max_jobs=args.max_jobs,config_path=args.config)
                except Exception as exc: print('CYCLE_FAILED',type(exc).__name__,exc,file=sys.stderr)
                n+=1; time.sleep(args.interval_seconds)
    return 0
if __name__=='__main__': raise SystemExit(main())
