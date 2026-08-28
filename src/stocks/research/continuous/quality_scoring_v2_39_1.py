from __future__ import annotations
from dataclasses import dataclass,asdict
import math
from .evidence_taxonomy_v2_39_1 import *

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception: return None

def _truthy(v):
    if isinstance(v,bool): return v
    return str(v).strip().lower() in {'1','true','yes','y','pass','passed','validated'}

def _metric(records, keys):
    vals=[]
    for r in records:
        for k in keys:
            n=_num(r.get('metrics',{}).get(k))
            if n is not None: vals.append(n); break
    return vals

def _records(records, cls): return [r for r in records if evidence_class(r.get('evidence_type',''))==cls]

def _positive_metric_score(records):
    vals=_metric(records,('quality_score','validation_score','robustness_score','wfe','psr','probabilistic_sharpe_ratio'))
    if not vals: return 0.5 if records else 0.0
    norm=[]
    for x in vals:
        if x>1 and x<=100: x/=100.0
        norm.append(max(0.0,min(1.0,x)))
    return sum(norm)/len(norm)

def _net_positive(records):
    for r in records:
        m=r.get('metrics',{})
        for key in ('net_edge_bps','mean_net_edge_bps','median_test_expectancy_bps','expectancy_bps','realized_net_return_bps'):
            n=_num(m.get(key))
            if n is not None: return n>0
        n=_num(m.get('net_return'))
        if n is not None: return n>0
        if _truthy(m.get('passed')) or str(m.get('status','')).upper() in {'PASS','PASSED','VALIDATED','ACCEPT'}: return True
    return False

@dataclass(frozen=True)
class QualityScoreV2391:
    total: float
    components: dict[str,float]
    penalty: float
    def as_dict(self): return asdict(self)

def quality_score(*, latest_registry: dict, records: list[dict], shadow_trades: int, posterior_net_edge_bps: float|None, breadth, fresh_hours: float, weights: dict, drift_severity: float, decay_severity: float, disagreement: float, minimum_shadow_trades: int) -> QualityScoreV2391:
    val=str(latest_registry.get('validation_status') or '').upper()
    validation=1.0 if val=='VALIDATED' else (.55 if val=='PROVISIONAL' else 0.0)
    cross=1.0 if _truthy(latest_registry.get('cross_engine_validated')) else 0.0
    generalization=1.0 if _truthy(latest_registry.get('dynamic_universe_generalized')) else 0.0
    oos=_records(records,OOS_VALIDATION); cost=_records(records,COST_ROBUSTNESS); cal=_records(records,CALIBRATION)
    oos_score=(.6 if _net_positive(oos) else .15 if oos else 0.0) + .4*_positive_metric_score(oos) if oos else 0.0
    oos_score=max(0.0,min(1.0,oos_score))
    cost_score=0.0
    if cost:
        max_mult=max([_num(r.get('metrics',{}).get('stress_multiplier')) or 1.0 for r in cost],default=1.0)
        cost_score=(.65 if _net_positive(cost) else .15)+.35*min(1.0,max_mult/3.0)
    shadow_coverage=min(1.0,shadow_trades/max(1,int(minimum_shadow_trades)))
    posterior_strength=0.0 if posterior_net_edge_bps is None else max(0.0,min(1.0,float(posterior_net_edge_bps)/20.0))
    shadow_score=.55*shadow_coverage+.45*posterior_strength
    calibration=_positive_metric_score(cal)
    class_target=max(1,int(weights.get('_minimum_classes',2))); source_target=max(1,int(weights.get('_minimum_sources',2)))
    breadth_score=.5*min(1.0,len(breadth.independent_classes)/class_target)+.5*min(1.0,len(breadth.independent_sources)/source_target)
    freshness=1.0 if breadth.fresh_outcome_classes else 0.0
    components={'statistical_validation':validation,'oos_robustness':oos_score,'cost_robustness':max(0,min(1,cost_score)),'shadow_evidence':shadow_score,'cross_engine':cross,'generalization':generalization,'calibration':calibration,'evidence_breadth':breadth_score,'freshness':freshness}
    default_weights={'statistical_validation':.15,'oos_robustness':.15,'cost_robustness':.15,'shadow_evidence':.15,'cross_engine':.10,'generalization':.10,'calibration':.05,'evidence_breadth':.10,'freshness':.05}
    ww={k:float(weights.get(k,v)) for k,v in default_weights.items()}; totalw=sum(ww.values()) or 1.0
    base=sum(components[k]*ww[k] for k in components)/totalw
    penalty=min(.45,.15*max(0,min(1,drift_severity))+.15*max(0,min(1,decay_severity))+.10*max(0,min(1,disagreement)))
    return QualityScoreV2391(float(max(0,min(1,base-penalty))),{k:float(v) for k,v in components.items()},float(penalty))

__all__=['QualityScoreV2391','quality_score']
