from __future__ import annotations
from datetime import datetime, timedelta, timezone
from .store_v2_39 import ResearchStoreV239, parse_utc, utc_now

def _hours(entity: dict, policy: dict) -> int:
    h=entity['health']; r=entity['role']
    if h=='DEGRADED': return int(policy.get('degraded_revalidation_hours',12))
    if h in {'WATCH','QUARANTINED'}: return int(policy.get('watch_revalidation_hours',24))
    if r=='CHAMPION': return int(policy.get('champion_revalidation_hours',168))
    if r=='CHALLENGER': return int(policy.get('challenger_revalidation_hours',72))
    return int(policy.get('candidate_revalidation_hours',24))

def priority(entity: dict) -> int:
    if entity['health']=='QUARANTINED': return 100
    if entity['health']=='DEGRADED': return 95
    if entity['health']=='WATCH': return 90
    if entity['role']=='CHAMPION': return 80
    if entity['role']=='CHALLENGER': return 70
    return 50

def next_due(entity: dict, policy: dict) -> str:
    return (datetime.now(timezone.utc)+timedelta(hours=_hours(entity,policy))).isoformat(timespec='seconds')

def schedule_due_entity_reviews(store: ResearchStoreV239, policy: dict) -> int:
    now=datetime.now(timezone.utc); count=0
    for e in store.list_entities(active_only=True):
        due=parse_utc(e.get('next_due_at'))
        if due is None or due<=now:
            bucket=now.strftime('%Y%m%d%H')
            store.enqueue('ENTITY_REVALIDATION',entity_id=e['entity_id'],priority=priority(e),payload={},max_attempts=int(policy.get('max_attempts',3)),dedupe_key=f"ENTITY_REVALIDATION:{e['entity_id']}:{bucket}")
            count+=1
    return count

def schedule_discovery_if_due(store: ResearchStoreV239, policy: dict, *, force: bool=False, limit: int=150, as_of: str | None=None) -> bool:
    last=parse_utc(store.latest_success_time('DISCOVERY_REFRESH'))
    due=last is None or (datetime.now(timezone.utc)-last).total_seconds()>=3600*int(policy.get('discovery_refresh_hours',24))
    if not (force or due): return False
    bucket=datetime.now(timezone.utc).strftime('%Y%m%d%H')
    store.enqueue('DISCOVERY_REFRESH',priority=60,payload={'limit':int(limit),'as_of':as_of},max_attempts=int(policy.get('max_attempts',3)),dedupe_key=f'DISCOVERY_REFRESH:{bucket}')
    return True

__all__=["next_due","priority","schedule_discovery_if_due","schedule_due_entity_reviews"]
