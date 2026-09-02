from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from .store_v2_39 import parse_utc

UPSTREAM_METADATA = 'UPSTREAM_METADATA'
STATISTICAL_VALIDATION = 'STATISTICAL_VALIDATION'
OOS_VALIDATION = 'OOS_VALIDATION'
COST_ROBUSTNESS = 'COST_ROBUSTNESS'
SHADOW_OUTCOME = 'SHADOW_OUTCOME'
CALIBRATION = 'CALIBRATION'
CROSS_ENGINE = 'CROSS_ENGINE'
GENERALIZATION = 'GENERALIZATION'
DRIFT_MONITOR = 'DRIFT_MONITOR'
OTHER = 'OTHER'

_METADATA_TYPES={'REGISTRY_SNAPSHOT','CANDIDATE_REGISTRY','UPSTREAM_METADATA'}
_OOS_TYPES={'OOS','OOS_VALIDATION','PURGED_WALK_FORWARD','WALK_FORWARD','HOLDOUT','HOLDOUT_VALIDATION','RL_OOS','FORWARD_VALIDATION'}
_COST_TYPES={'COST_STRESS','EXECUTION_COST_STRESS','COST_ROBUSTNESS','IMPLEMENTATION_SHORTFALL_STRESS'}
_SHADOW_TYPES={'SHADOW_TRADE','SHADOW_OUTCOME','FORWARD_SHADOW'}
_CAL_TYPES={'FORECAST_CALIBRATION','COST_CALIBRATION','CALIBRATION'}
_CROSS_TYPES={'CROSS_ENGINE','CROSS_ENGINE_RESULT','CROSS_ENGINE_VALIDATION'}
_GEN_TYPES={'GENERALIZATION','GENERALIZATION_RESULT','DYNAMIC_UNIVERSE_GENERALIZATION'}
_STAT_TYPES={'STATISTICAL_VALIDATION','V233_VALIDATION','ANTI_OVERFIT_VALIDATION'}
_DRIFT_TYPES={'DRIFT','FEATURE_DRIFT','MODEL_DRIFT'}

INDEPENDENT_OUTCOME_CLASSES={STATISTICAL_VALIDATION,OOS_VALIDATION,COST_ROBUSTNESS,SHADOW_OUTCOME,CALIBRATION,CROSS_ENGINE,GENERALIZATION}
PROMOTION_OUTCOME_CLASSES={STATISTICAL_VALIDATION,OOS_VALIDATION,COST_ROBUSTNESS,SHADOW_OUTCOME,CALIBRATION}

@dataclass(frozen=True)
class EvidenceBreadthV2391:
    independent_classes: tuple[str,...]
    independent_sources: tuple[str,...]
    fresh_outcome_classes: tuple[str,...]
    latest_outcome_time: str|None
    def as_dict(self):
        return {'independent_classes':self.independent_classes,'independent_sources':self.independent_sources,'fresh_outcome_classes':self.fresh_outcome_classes,'latest_outcome_time':self.latest_outcome_time}

def evidence_class(evidence_type: str) -> str:
    t=str(evidence_type or '').strip().upper()
    if t in _METADATA_TYPES: return UPSTREAM_METADATA
    if t in _OOS_TYPES: return OOS_VALIDATION
    if t in _COST_TYPES: return COST_ROBUSTNESS
    if t in _SHADOW_TYPES: return SHADOW_OUTCOME
    if t in _CAL_TYPES: return CALIBRATION
    if t in _CROSS_TYPES: return CROSS_ENGINE
    if t in _GEN_TYPES: return GENERALIZATION
    if t in _STAT_TYPES: return STATISTICAL_VALIDATION
    if t in _DRIFT_TYPES: return DRIFT_MONITOR
    return OTHER

def source_group(record: dict) -> str:
    source=str(record.get('source') or '').strip().lower()
    # Source groups are intentionally coarse: different files produced by the same
    # engine are correlated evidence, not independent votes.
    for marker,group in (
        ('v2.37','shadow_v237'),('shadow','shadow_v237'),('v2.36','execution_v236'),('execution','execution_v236'),
        ('v2.33','stat_validation_v233'),('statistical','stat_validation_v233'),('walk','oos_validation'),('holdout','oos_validation'),
        ('lean','cross_engine'),('nautilus','cross_engine'),('pybroker','cross_engine'),('cross_engine','cross_engine'),
        ('generalization','generalization'),('dynamic_universe','generalization'),('v2.38','rl_v238'),('rl','rl_v238'),
        ('forecast','forecast'),('calibration','calibration'),('research_candidate_registry','registry_metadata'),('registry','registry_metadata')):
        if marker in source: return group
    return source or 'unknown'

def evidence_breadth(records: Iterable[dict], *, fresh_hours: float=720.0, now: datetime|None=None) -> EvidenceBreadthV2391:
    now=now or datetime.now(timezone.utc); classes=set(); sources=set(); fresh=set(); latest=None
    for r in records:
        cls=evidence_class(r.get('evidence_type',''))
        if cls not in INDEPENDENT_OUTCOME_CLASSES: continue
        classes.add(cls); sources.add(source_group(r))
        dt=parse_utc(r.get('as_of'))
        if dt and (latest is None or dt>latest): latest=dt
        if dt and (now-dt).total_seconds() <= float(fresh_hours)*3600: fresh.add(cls)
    return EvidenceBreadthV2391(tuple(sorted(classes)),tuple(sorted(sources)),tuple(sorted(fresh)),latest.isoformat() if latest else None)

__all__=['UPSTREAM_METADATA','STATISTICAL_VALIDATION','OOS_VALIDATION','COST_ROBUSTNESS','SHADOW_OUTCOME','CALIBRATION','CROSS_ENGINE','GENERALIZATION','DRIFT_MONITOR','OTHER','INDEPENDENT_OUTCOME_CLASSES','PROMOTION_OUTCOME_CLASSES','EvidenceBreadthV2391','evidence_class','source_group','evidence_breadth']
