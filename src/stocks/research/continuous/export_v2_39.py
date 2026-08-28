from __future__ import annotations
import csv, json
from pathlib import Path
from .store_v2_39 import ResearchStoreV239, utc_now

def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text('',encoding='utf-8'); return
    keys=sorted({k for r in rows for k in r if k not in {'metadata','payload','reasons'}})
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows({k:r.get(k) for k in keys} for r in rows)

def export_snapshot(runtime_root: Path, store: ResearchStoreV239) -> dict:
    runtime_root.mkdir(parents=True,exist_ok=True)
    entities=store.list_entities(); recs=store.latest_recommendations(); jobs=store.jobs(); attempts=store.job_attempts(); experiments=store.experiments(); latest_evidence=store.latest_evidence_rows(); counts=store.counts()
    _write_csv(runtime_root/'entities.csv',entities); _write_csv(runtime_root/'champion_challenger.csv',[e for e in entities if e.get('role') in {'CHAMPION','CHALLENGER'}]); _write_csv(runtime_root/'recommendations.csv',recs); _write_csv(runtime_root/'retirement_watch.csv',[r for r in recs if 'RETIRE' in r.get('action','') or 'DEACTIVATE' in r.get('action','')]); _write_csv(runtime_root/'job_queue.csv',jobs); _write_csv(runtime_root/'job_attempts.csv',attempts); _write_csv(runtime_root/'experiments.csv',experiments); _write_csv(runtime_root/'latest_evidence.csv',latest_evidence)
    status={'schema':'continuous_quant_research_status_v2_39','generated_at':utc_now(),'counts':counts,'recommendations':recs[:20],
            'automatic_champion_promotion':False,'automatic_live_promotion':False,'broker_submission_enabled':False,'order_calls':0,'execution_authority':'NONE'}
    (runtime_root/'status.json').write_text(json.dumps(status,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    lines=['# Continuous Quant Research v2.39','',f"Generated: {status['generated_at']}",'',f"Active entities: {sum(x['n'] for x in counts['entities'])}",f"Evidence rows: {counts['evidence']}",'','## Latest recommendations','']
    for r in recs[:20]: lines.append(f"- `{r['entity_id']}` — **{r['action']}** — score {float(r['score']):.3f}")
    lines += ['','Execution authority: **NONE**','Automatic live promotion: **false**']
    (runtime_root/'status.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return status

__all__=["export_snapshot"]
