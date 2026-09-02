from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pandas as pd
from .contracts_v2_39 import EntityV239, EvidenceRecordV239, ResearchRole
from .store_v2_39 import ResearchStoreV239

def _role(stage: str) -> str:
    s=str(stage).upper()
    return ResearchRole.CHALLENGER.value if s in {"FINALIST_CANDIDATE","CHALLENGER"} else ResearchRole.CANDIDATE.value

def _clean(v):
    if pd.isna(v): return None
    if hasattr(v,"item"):
        try: return v.item()
        except Exception: pass
    return v

def sync_candidate_registry(project_root: Path, store: ResearchStoreV239, *, rebuild: bool=True) -> dict:
    if rebuild:
        try:
            from stocks.research.research_candidate_registry import write_research_candidate_registry
            frame, audit, path = write_research_candidate_registry(project_root)
        except Exception:
            path=project_root/'artifacts/research_runtime/research_candidate_registry/registry.csv'
            frame=pd.read_csv(path) if path.is_file() and path.stat().st_size else pd.DataFrame(); audit={}
    else:
        path=project_root/'artifacts/research_runtime/research_candidate_registry/registry.csv'
        frame=pd.read_csv(path) if path.is_file() and path.stat().st_size else pd.DataFrame(); audit={}
    store.mark_registry_entities_inactive()
    inserted_evidence=0
    mtime = path.stat().st_mtime_ns if path.is_file() else 0
    for row in frame.to_dict(orient='records'):
        hid=str(row.get('hypothesis_id') or '').strip()
        if not hid: continue
        entity_id=f"STRATEGY:{hid}"
        clean={str(k):_clean(v) for k,v in row.items()}
        store.upsert_entity(EntityV239(entity_id,'STRATEGY',str(clean.get('family') or 'UNKNOWN'),'CANDIDATE_REGISTRY','v2.39',_role(clean.get('promotion_stage','')),metadata=clean),active=True)
        metrics={k:clean.get(k) for k in ('research_status','validation_status','promotion_stage','cross_engine_status','cross_engine_validated','generalization_status','dynamic_universe_generalized','robustness_score','median_test_expectancy_bps','median_stress_test_expectancy_bps','median_test_profit_factor','queue_rank') if k in clean}
        fingerprint=hashlib.sha256(json.dumps(metrics,sort_keys=True,default=str).encode()).hexdigest()[:16]
        ev=EvidenceRecordV239(entity_id,'REGISTRY_SNAPSHOT',pd.Timestamp(path.stat().st_mtime,unit='s',tz='UTC').isoformat() if path.is_file() else pd.Timestamp.utcnow().isoformat(),metrics,'research_candidate_registry',f"{path}:{mtime}:{fingerprint}",sample_count=1)
        inserted_evidence += int(store.add_evidence(ev))
    return {"candidate_count":len(frame),"inserted_evidence":inserted_evidence,"path":str(path),"registry_audit":audit}

__all__=["sync_candidate_registry"]
