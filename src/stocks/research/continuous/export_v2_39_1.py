from __future__ import annotations
import csv,json
from pathlib import Path
from .health_v2_39_1 import assess_entity_hardened
from .store_v2_39 import ResearchStoreV239,utc_now

def _write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text('',encoding='utf-8');return
    keys=sorted({k for r in rows for k in r if not isinstance(r.get(k),(dict,list,tuple))})
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r.get(k) for k in keys} for r in rows)

def export_hardened_snapshot(runtime_root:Path,store:ResearchStoreV239,*,cfg:dict)->dict:
    runtime_root.mkdir(parents=True,exist_ok=True);entities=store.list_entities();assess=[]
    for e in entities:
        if not e.get('is_active'):continue
        a=assess_entity_hardened(store,e['entity_id'],policy=cfg['health'],bayesian=cfg['bayesian'],quality_weights=cfg['quality_weights']);d=a.as_dict();d['role']=e['role'];d['family']=e['family'];assess.append(d)
    recs=store.latest_recommendations();counts=store.counts()
    flat=[]
    for a in assess:
        flat.append({'entity_id':a['entity_id'],'role':a['role'],'family':a['family'],'health':a['health'],'recommendation':a['recommendation'],'quality_score':a['score'],'gate_passed':a['gate_passed'],'shadow_trades':a['shadow_trades'],'independent_classes':a['independent_classes'],'independent_sources':a['independent_sources'],'posterior_net_edge_bps':a['posterior_net_edge_bps'],'blockers':'|'.join(a['blockers']),'warnings':'|'.join(a['warnings']),'missing_requirements':'|'.join(a['missing_requirements']),'positive_reasons':'|'.join(a['positive_reasons'])})
    _write(runtime_root/'quality_scorecard_v2_39_1.csv',flat);_write(runtime_root/'champion_review_queue_v2_39_1.csv',[x for x in flat if x['recommendation']=='RECOMMEND_CHAMPION_REVIEW']);_write(runtime_root/'evidence_gaps_v2_39_1.csv',[x for x in flat if x['missing_requirements']]);_write(runtime_root/'retirement_watch_v2_39_1.csv',[x for x in flat if 'RETIRE' in x['recommendation'] or 'DEACTIVATE' in x['recommendation']])
    status={'schema':'continuous_quant_research_status_v2_39_1','generated_at':utc_now(),'counts':counts,'assessments':assess,'recommendations':recs[:20],'champion_review_count':sum(a['recommendation']=='RECOMMEND_CHAMPION_REVIEW' for a in assess),'automatic_champion_promotion':False,'automatic_live_promotion':False,'broker_submission_enabled':False,'order_calls':0,'execution_authority':'NONE'}
    (runtime_root/'status_v2_39_1.json').write_text(json.dumps(status,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    lines=['# Continuous Quant Research v2.39.1','',f"Generated: {status['generated_at']}",'',f"Active entities: {sum(x['n'] for x in counts['entities'])}",f"Champion reviews eligible: {status['champion_review_count']}",'','## Hardened assessments','']
    for x in sorted(flat,key=lambda y:y['quality_score'],reverse=True)[:30]:lines.append(f"- `{x['entity_id']}` — **{x['recommendation']}** — quality {x['quality_score']:.3f} — missing: {x['missing_requirements'] or 'none'}")
    lines += ['','Execution authority: **NONE**','Automatic champion promotion: **false**','Automatic live promotion: **false**']
    (runtime_root/'status_v2_39_1.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return status

__all__=['export_hardened_snapshot']
