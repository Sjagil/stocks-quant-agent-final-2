from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import math
from .bayesian_shrinkage_v2_39 import shrink_mean
from .champion_gate_v2_39_1 import evaluate_champion_gate
from .contracts_v2_39 import ResearchHealth
from .disagreement_v2_39 import robust_disagreement
from .drift_decay_v2_39 import performance_decay
from .evidence_taxonomy_v2_39_1 import evidence_breadth
from .quality_scoring_v2_39_1 import quality_score
from .store_v2_39 import ResearchStoreV239,parse_utc

def _num(v):
    try:
        x=float(v);return x if math.isfinite(x) else None
    except Exception:return None

def _truthy(v):
    if isinstance(v,bool):return v
    return str(v).strip().lower() in {'1','true','yes','y'}

@dataclass(frozen=True)
class HardenedAssessmentV2391:
    entity_id:str; health:str; recommendation:str; score:float
    positive_reasons:tuple[str,...]; blockers:tuple[str,...]; warnings:tuple[str,...]; missing_requirements:tuple[str,...]
    posterior_net_edge_bps:float|None; shadow_trades:int; independent_sources:int; independent_classes:int
    drift_severity:float; decay_severity:float; disagreement:float; quality_components:dict[str,float]; gate_passed:bool
    execution_authority:str='NONE'
    @property
    def reasons(self): return self.positive_reasons+self.blockers+self.warnings+self.missing_requirements
    def as_dict(self):
        d=asdict(self); d['reasons']=self.reasons; return d

def assess_entity_hardened(store:ResearchStoreV239,entity_id:str,*,policy:dict,bayesian:dict,quality_weights:dict)->HardenedAssessmentV2391:
    ent=store.get_entity(entity_id)
    if ent is None:raise KeyError(entity_id)
    if ent['role']=='RETIRED':return HardenedAssessmentV2391(entity_id,'RETIRED','HOLD_RETIRED',0.0,(),('MANUALLY_RETIRED',),(),(),None,0,0,0,0,0,0,{},False)
    ev=store.evidence_for(entity_id); registry=[x for x in ev if x['evidence_type']=='REGISTRY_SNAPSHOT']; latest_reg=registry[-1]['metrics'] if registry else {}
    val=str(latest_reg.get('validation_status') or '').upper(); promotion=str(latest_reg.get('promotion_stage') or '').upper()
    shadow=[x for x in ev if x['evidence_type']=='SHADOW_TRADE']; returns=[_num(x['metrics'].get('realized_net_return_bps')) for x in shadow]; returns=[x for x in returns if x is not None]
    shr=shrink_mean(returns,prior_mean=float(bayesian.get('prior_mean_bps',0)),prior_strength=float(bayesian.get('prior_strength',20)))
    decay=performance_decay(returns)
    drift_ev=[x for x in ev if x['evidence_type']=='DRIFT']; psi=max([_num(x['metrics'].get('psi_max')) or 0 for x in drift_ev],default=0); js=max([_num(x['metrics'].get('js_max')) or 0 for x in drift_ev],default=0)
    drift_sev=max(min(1,psi/max(float(policy.get('psi_quarantine',.25)),1e-12)),min(1,js/max(float(policy.get('js_quarantine',.2)),1e-12)))
    scores=[]
    for x in ev:
        if x['evidence_type']=='REGISTRY_SNAPSHOT':continue
        for k in ('quality_score','validation_score','score'):
            n=_num(x['metrics'].get(k))
            if n is not None:scores.append(n/100 if 1<abs(n)<=100 else n);break
    disagreement=robust_disagreement(scores)
    warnings=[]; severe=[]
    latest=store.latest_evidence_time(entity_id); stale=True
    if latest:
        age=(datetime.now(timezone.utc)-parse_utc(latest)).total_seconds()/3600; stale=age>float(policy.get('stale_evidence_hours',168))
    if stale:warnings.append('EVIDENCE_STALE')
    if val=='REJECTED' or promotion.startswith('REJECTED'):severe.append('UPSTREAM_VALIDATION_REJECTED')
    if psi>=float(policy.get('psi_quarantine',.25)) or js>=float(policy.get('js_quarantine',.2)):severe.append('SEVERE_DRIFT')
    elif psi>=float(policy.get('psi_watch',.1)) or js>=float(policy.get('js_watch',.08)):warnings.append('DRIFT_WATCH')
    if decay.severity>=float(policy.get('decay_quarantine',.7)):severe.append('SEVERE_PERFORMANCE_DECAY')
    elif decay.severity>=float(policy.get('decay_watch',.35)):warnings.append('PERFORMANCE_DECAY_WATCH')
    if disagreement>=float(policy.get('disagreement_quarantine',.75)):severe.append('SEVERE_ENSEMBLE_DISAGREEMENT')
    elif disagreement>=float(policy.get('disagreement_watch',.45)):warnings.append('ENSEMBLE_DISAGREEMENT_WATCH')
    if returns and shr.posterior_mean<float(policy.get('minimum_posterior_net_edge_bps',0)):severe.append('POSTERIOR_NET_EDGE_NEGATIVE')
    breadth=evidence_breadth(ev,fresh_hours=float(policy.get('promotion_evidence_fresh_hours',720)))
    qw=dict(quality_weights); qw['_minimum_classes']=int(policy.get('minimum_independent_evidence_classes',2)); qw['_minimum_sources']=int(policy.get('minimum_independent_evidence_sources',2))
    q=quality_score(latest_registry=latest_reg,records=ev,shadow_trades=len(returns),posterior_net_edge_bps=None if shr.observations==0 else shr.posterior_mean,breadth=breadth,fresh_hours=float(policy.get('promotion_evidence_fresh_hours',720)),weights=qw,drift_severity=drift_sev,decay_severity=decay.severity,disagreement=disagreement,minimum_shadow_trades=int(policy.get('minimum_shadow_trades_for_promotion_review',30)))
    gate=evaluate_champion_gate(latest_registry=latest_reg,records=ev,breadth=breadth,shadow_trades=len(returns),posterior_net_edge_bps=None if shr.observations==0 else shr.posterior_mean,quality_score=q.total,policy=policy,severe_reasons=set(severe))
    if severe:health=ResearchHealth.QUARANTINED.value
    elif warnings:health=ResearchHealth.WATCH.value
    elif not ev:health=ResearchHealth.NEW.value
    else:health=ResearchHealth.HEALTHY.value
    role=ent['role']
    if role=='CHAMPION':rec='RECOMMEND_DEACTIVATE' if health=='QUARANTINED' else ('RECOMMEND_REVALIDATE' if health=='WATCH' else 'HOLD_CHAMPION')
    elif health=='QUARANTINED':rec='RECOMMEND_RETIRE_REVIEW' if 'UPSTREAM_VALIDATION_REJECTED' in severe else 'REJECT_OR_REWORK'
    elif health=='WATCH':rec='REVALIDATE'
    elif gate.passed:rec='RECOMMEND_CHAMPION_REVIEW'
    else:rec='ACCUMULATE_EVIDENCE'
    return HardenedAssessmentV2391(entity_id,health,rec,q.total,gate.positive_reasons,tuple(dict.fromkeys(severe+list(gate.blockers))),tuple(dict.fromkeys(warnings)),gate.missing_requirements,None if shr.observations==0 else shr.posterior_mean,len(returns),len(breadth.independent_sources),len(breadth.independent_classes),drift_sev,decay.severity,disagreement,q.components,gate.passed)

__all__=['HardenedAssessmentV2391','assess_entity_hardened']
