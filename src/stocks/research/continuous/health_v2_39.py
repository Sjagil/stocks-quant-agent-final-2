from __future__ import annotations
from datetime import datetime, timezone
import math
from .bayesian_shrinkage_v2_39 import shrink_mean
from .contracts_v2_39 import HealthAssessmentV239, ResearchHealth
from .disagreement_v2_39 import robust_disagreement
from .drift_decay_v2_39 import performance_decay
from .store_v2_39 import ResearchStoreV239, parse_utc

def _truthy(v):
    if isinstance(v,bool): return v
    return str(v).strip().lower() in {"1","true","yes","y"}

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception: return None

def assess_entity(store: ResearchStoreV239, entity_id: str, *, policy: dict, bayesian: dict) -> HealthAssessmentV239:
    ent=store.get_entity(entity_id)
    if ent is None: raise KeyError(entity_id)
    if ent['role']=='RETIRED': return HealthAssessmentV239(entity_id,ResearchHealth.RETIRED.value,'HOLD_RETIRED',0.0,('MANUALLY_RETIRED',))
    ev=store.evidence_for(entity_id); reasons=[]
    registry=[x for x in ev if x['evidence_type']=='REGISTRY_SNAPSHOT']
    latest_reg=registry[-1]['metrics'] if registry else {}
    val=str(latest_reg.get('validation_status') or '').upper(); promotion=str(latest_reg.get('promotion_stage') or '').upper()
    cross=_truthy(latest_reg.get('cross_engine_validated',False)); generalized=_truthy(latest_reg.get('dynamic_universe_generalized',False))
    if val=='REJECTED' or promotion.startswith('REJECTED'):
        reasons.append('UPSTREAM_VALIDATION_REJECTED')
    shadow=[x for x in ev if x['evidence_type']=='SHADOW_TRADE']
    shadow_returns=[_num(x['metrics'].get('realized_net_return_bps')) for x in shadow]; shadow_returns=[x for x in shadow_returns if x is not None]
    shr=shrink_mean(shadow_returns,prior_mean=float(bayesian.get('prior_mean_bps',0)),prior_strength=float(bayesian.get('prior_strength',20)))
    decay=performance_decay(shadow_returns)
    drift_ev=[x for x in ev if x['evidence_type']=='DRIFT']
    psi=max([_num(x['metrics'].get('psi_max')) or 0.0 for x in drift_ev],default=0.0)
    js=max([_num(x['metrics'].get('js_max')) or 0.0 for x in drift_ev],default=0.0)
    drift_sev=max(min(1,psi/max(float(policy.get('psi_quarantine',.25)),1e-12)),min(1,js/max(float(policy.get('js_quarantine',.20)),1e-12)))
    scores=[]; sources=set()
    for x in ev:
        sources.add(x['source'])
        for key in ('quality_score','validation_score','score'):
            n=_num(x['metrics'].get(key))
            if n is not None:
                scores.append(n/100.0 if abs(n)>1.0 and abs(n)<=100.0 else n); break
    disagreement=robust_disagreement(scores)
    latest=store.latest_evidence_time(entity_id); stale=False
    if latest:
        age=(datetime.now(timezone.utc)-parse_utc(latest)).total_seconds()/3600.0
        stale=age>float(policy.get('stale_evidence_hours',168))
    else: stale=True
    if stale: reasons.append('EVIDENCE_STALE')
    if psi>=float(policy.get('psi_quarantine',.25)) or js>=float(policy.get('js_quarantine',.20)): reasons.append('SEVERE_DRIFT')
    elif psi>=float(policy.get('psi_watch',.10)) or js>=float(policy.get('js_watch',.08)): reasons.append('DRIFT_WATCH')
    if decay.severity>=float(policy.get('decay_quarantine',.70)): reasons.append('SEVERE_PERFORMANCE_DECAY')
    elif decay.severity>=float(policy.get('decay_watch',.35)): reasons.append('PERFORMANCE_DECAY_WATCH')
    if disagreement>=float(policy.get('disagreement_quarantine',.75)): reasons.append('SEVERE_ENSEMBLE_DISAGREEMENT')
    elif disagreement>=float(policy.get('disagreement_watch',.45)): reasons.append('ENSEMBLE_DISAGREEMENT_WATCH')
    if shadow_returns and shr.posterior_mean<float(policy.get('minimum_posterior_net_edge_bps',0)): reasons.append('POSTERIOR_NET_EDGE_NEGATIVE')
    severe={'UPSTREAM_VALIDATION_REJECTED','SEVERE_DRIFT','SEVERE_PERFORMANCE_DECAY','SEVERE_ENSEMBLE_DISAGREEMENT','POSTERIOR_NET_EDGE_NEGATIVE'}
    watch={'EVIDENCE_STALE','DRIFT_WATCH','PERFORMANCE_DECAY_WATCH','ENSEMBLE_DISAGREEMENT_WATCH'}
    if severe.intersection(reasons): health=ResearchHealth.QUARANTINED.value
    elif watch.intersection(reasons): health=ResearchHealth.WATCH.value
    elif not ev: health=ResearchHealth.NEW.value
    else: health=ResearchHealth.HEALTHY.value
    role=ent['role']; min_trades=int(policy.get('minimum_shadow_trades_for_promotion_review',30)); min_sources=int(policy.get('minimum_independent_evidence_sources',2))
    upstream_ok=(val in {'VALIDATED','PROVISIONAL',''} and not str(promotion).startswith('REJECTED'))
    evidence_ok=(len(shadow_returns)>=min_trades and len(sources)>=min_sources) or (cross and generalized and len(sources)>=1)
    if role=='CHAMPION':
        recommendation='RECOMMEND_DEACTIVATE' if health==ResearchHealth.QUARANTINED.value else ('RECOMMEND_REVALIDATE' if health==ResearchHealth.WATCH.value else 'HOLD_CHAMPION')
    elif health==ResearchHealth.QUARANTINED.value: recommendation='RECOMMEND_RETIRE_REVIEW' if ('UPSTREAM_VALIDATION_REJECTED' in reasons or len(shadow_returns)>=int(policy.get('retirement_failure_streak',3))) else 'REJECT_OR_REWORK'
    elif health==ResearchHealth.WATCH.value: recommendation='REVALIDATE'
    elif health==ResearchHealth.HEALTHY.value and upstream_ok and evidence_ok: recommendation='RECOMMEND_CHAMPION_REVIEW'
    else: recommendation='ACCUMULATE_EVIDENCE'
    quality=1.0
    if health==ResearchHealth.WATCH.value: quality=.65
    elif health==ResearchHealth.QUARANTINED.value: quality=.10
    elif health==ResearchHealth.NEW.value: quality=.35
    quality*=max(0.0,1.0-.35*drift_sev-.30*decay.severity-.20*disagreement)
    return HealthAssessmentV239(entity_id,health,recommendation,float(max(0,min(1,quality))),tuple(reasons),None if shr.observations==0 else shr.posterior_mean,len(shadow_returns),len(sources),float(drift_sev),float(decay.severity),float(disagreement))

__all__=["assess_entity"]
