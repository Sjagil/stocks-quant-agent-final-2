from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import math
from .evidence_taxonomy_v2_39_1 import *

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def _truthy(v):
    if isinstance(v,bool): return v
    return str(v).strip().lower() in {'1','true','yes','y','pass','passed','validated'}

def _sample_count(record):
    m=record.get('metrics',{}); candidates=[record.get('sample_count')]
    for k in ('observations','n_obs','n','trades','trade_count','sample_count'): candidates.append(m.get(k))
    vals=[int(float(x)) for x in candidates if _num(x) is not None and float(x)>=0]
    return max(vals,default=0)

def _positive(record):
    m=record.get('metrics',{})
    for k in ('net_edge_bps','mean_net_edge_bps','median_test_expectancy_bps','expectancy_bps','realized_net_return_bps','median_stress_test_expectancy_bps'):
        n=_num(m.get(k))
        if n is not None:return n>0
    n=_num(m.get('net_return'))
    if n is not None:return n>0
    return _truthy(m.get('passed')) or str(m.get('status','')).upper() in {'PASS','PASSED','VALIDATED','ACCEPT'}

@dataclass(frozen=True)
class ChampionGateV2391:
    passed: bool
    positive_reasons: tuple[str,...]
    blockers: tuple[str,...]
    missing_requirements: tuple[str,...]
    independent_classes: tuple[str,...]
    independent_sources: tuple[str,...]
    oos_observations: int
    shadow_trades: int
    cost_stress_max_multiplier: float
    quality_score: float
    def as_dict(self): return asdict(self)

def evaluate_champion_gate(*, latest_registry:dict, records:list[dict], breadth, shadow_trades:int, posterior_net_edge_bps:float|None, quality_score:float, policy:dict, severe_reasons:set[str]|None=None)->ChampionGateV2391:
    severe_reasons=severe_reasons or set(); pos=[]; blockers=[]; missing=[]
    val=str(latest_registry.get('validation_status') or '').upper(); promotion=str(latest_registry.get('promotion_stage') or '').upper()
    cross=_truthy(latest_registry.get('cross_engine_validated')); generalized=_truthy(latest_registry.get('dynamic_universe_generalized'))
    if val=='VALIDATED':pos.append('UPSTREAM_VALIDATION_PASS')
    else:missing.append('NEED_UPSTREAM_VALIDATION_VALIDATED')
    if cross:pos.append('CROSS_ENGINE_VALIDATED')
    else:missing.append('NEED_CROSS_ENGINE_VALIDATION')
    if generalized:pos.append('DYNAMIC_UNIVERSE_GENERALIZED')
    else:missing.append('NEED_DYNAMIC_UNIVERSE_GENERALIZATION')
    if val=='REJECTED' or promotion.startswith('REJECTED'): blockers.append('UPSTREAM_VALIDATION_REJECTED')

    min_classes=int(policy.get('minimum_independent_evidence_classes',2)); min_sources=int(policy.get('minimum_independent_evidence_sources',2))
    if len(breadth.independent_classes)>=min_classes:pos.append('EVIDENCE_CLASS_BREADTH_SUFFICIENT')
    else:missing.append(f'NEED_{min_classes}_INDEPENDENT_EVIDENCE_CLASSES')
    if len(breadth.independent_sources)>=min_sources:pos.append('EVIDENCE_SOURCE_INDEPENDENCE_SUFFICIENT')
    else:missing.append(f'NEED_{min_sources}_INDEPENDENT_EVIDENCE_SOURCES')
    if breadth.fresh_outcome_classes:pos.append('FRESH_OUTCOME_EVIDENCE_PRESENT')
    elif policy.get('require_fresh_outcome_evidence',True):missing.append('NEED_FRESH_OUTCOME_EVIDENCE')

    oos=[r for r in records if evidence_class(r.get('evidence_type',''))==OOS_VALIDATION]
    oos_obs=sum(_sample_count(r) for r in oos); min_oos=int(policy.get('minimum_oos_observations',60))
    oos_ok=oos_obs>=min_oos and any(_positive(r) for r in oos)
    if oos_ok:pos.append('OOS_EVIDENCE_SUFFICIENT')

    min_shadow=int(policy.get('minimum_shadow_trades_for_promotion_review',30)); shadow_ok=shadow_trades>=min_shadow and posterior_net_edge_bps is not None and posterior_net_edge_bps>float(policy.get('minimum_posterior_net_edge_bps',0))
    if shadow_ok:pos.extend(['SHADOW_SAMPLE_SUFFICIENT','POSTERIOR_NET_EDGE_POSITIVE'])
    if not (oos_ok or shadow_ok):missing.append('NEED_POSITIVE_OOS_OR_SHADOW_EVIDENCE')

    cost=[r for r in records if evidence_class(r.get('evidence_type',''))==COST_ROBUSTNESS]
    min_mult=float(policy.get('minimum_cost_stress_multiplier',2.0)); max_mult=max([_num(r.get('metrics',{}).get('stress_multiplier')) or 1.0 for r in cost],default=0.0)
    cost_ok=any((_num(r.get('metrics',{}).get('stress_multiplier')) or 1.0)>=min_mult and _positive(r) for r in cost)
    if cost_ok:pos.append('COST_STRESS_PASS')
    elif policy.get('require_cost_robustness_for_champion_review',True):missing.append(f'NEED_POSITIVE_COST_STRESS_{min_mult:g}X')

    qmin=float(policy.get('minimum_quality_score_for_champion_review',.72))
    if quality_score>=qmin:pos.append('QUALITY_SCORE_SUFFICIENT')
    else:missing.append(f'NEED_QUALITY_SCORE_{qmin:.2f}')
    if severe_reasons:blockers.extend(sorted(severe_reasons))
    passed=not blockers and not missing
    if passed:pos.append('CHAMPION_REVIEW_GATE_PASS')
    return ChampionGateV2391(bool(passed),tuple(dict.fromkeys(pos)),tuple(dict.fromkeys(blockers)),tuple(dict.fromkeys(missing)),breadth.independent_classes,breadth.independent_sources,int(oos_obs),int(shadow_trades),float(max_mult),float(quality_score))

__all__=['ChampionGateV2391','evaluate_champion_gate']
