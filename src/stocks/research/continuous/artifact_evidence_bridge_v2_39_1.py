from __future__ import annotations
from pathlib import Path
import hashlib,json
import pandas as pd
from .contracts_v2_39 import EvidenceRecordV239
from .store_v2_39 import ResearchStoreV239,utc_now

def _read(path:Path):
    if not path.is_file() or path.stat().st_size==0:return pd.DataFrame()
    try:return pd.read_csv(path)
    except Exception:return pd.DataFrame()

def _clean(v):
    if pd.isna(v):return None
    if hasattr(v,'item'):
        try:return v.item()
        except Exception:pass
    return v

def _sample(row):
    for k in ('observations','n_obs','test_observations','trades','trade_count','n_trades','test_trades'):
        try:
            if row.get(k) is not None and not pd.isna(row.get(k)):return max(0,int(float(row.get(k))))
        except Exception:pass
    return 0

def _add_rows(store,path,evidence_type,source,*,require_existing=True,extra=None):
    frame=_read(path); seen=added=0
    if frame.empty or 'hypothesis_id' not in frame.columns:return {'path':str(path),'seen':0,'added':0}
    mtime=path.stat().st_mtime_ns
    for row in frame.to_dict(orient='records'):
        hid=str(row.get('hypothesis_id') or '').strip()
        if not hid:continue
        eid=f'STRATEGY:{hid}'
        if require_existing and store.get_entity(eid) is None:continue
        clean={str(k):_clean(v) for k,v in row.items()}
        if extra:clean.update(extra)
        fp=hashlib.sha256(json.dumps(clean,sort_keys=True,default=str).encode()).hexdigest()[:16]
        ev=EvidenceRecordV239(eid,evidence_type,pd.Timestamp(path.stat().st_mtime,unit='s',tz='UTC').isoformat(),clean,source,f'{path}:{mtime}:{fp}',_sample(clean))
        seen+=1;added+=int(store.add_evidence(ev))
    return {'path':str(path),'seen':seen,'added':added}

def sync_known_artifact_evidence(project_root:Path,store:ResearchStoreV239)->dict:
    specs=[
      ('artifacts/research_runtime/cross_engine_strategy_validation_v2_17/strategy_summary.csv','CROSS_ENGINE_RESULT','cross_engine_v217',None),
      ('artifacts/research_runtime/strategy_generation_v2_22/cross_engine/strategy_summary.csv','CROSS_ENGINE_RESULT','strategy_generation_cross_engine_v222',None),
      ('artifacts/research_runtime/dynamic_universe_generalization/summary.csv','GENERALIZATION_RESULT','dynamic_universe_generalization',None),
      ('artifacts/research_runtime/validated_strategy_registry/registry.csv','STATISTICAL_VALIDATION','validated_strategy_registry',None),
      ('artifacts/research_runtime/strategy_generation_v2_22/validation_queue.csv','OOS_VALIDATION','strategy_generation_validation_v222',None),
      # This queue contains a stress expectancy field, but the upstream artifact does not
      # guarantee the stress multiplier. It is deliberately imported without a multiplier,
      # so it can improve diagnostics but can never satisfy the hard 2x cost gate by itself.
      ('artifacts/research_runtime/strategy_generation_v2_22/validation_queue.csv','COST_STRESS','strategy_generation_validation_v222',{'stress_multiplier':1.0}),
    ]
    rows=[]
    for rel,etype,source,extra in specs:rows.append(_add_rows(store,project_root/rel,etype,source,extra=extra))
    return {'sources':rows,'seen':sum(x['seen'] for x in rows),'added':sum(x['added'] for x in rows)}

__all__=['sync_known_artifact_evidence']
