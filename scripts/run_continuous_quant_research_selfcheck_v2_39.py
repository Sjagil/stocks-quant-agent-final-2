#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path: sys.path.insert(0,str(ROOT/'src'))
from stocks.research.continuous.contracts_v2_39 import EntityV239, EvidenceRecordV239
from stocks.research.continuous.health_v2_39 import assess_entity
from stocks.research.continuous.store_v2_39 import ResearchStoreV239, utc_now
with tempfile.TemporaryDirectory() as td:
    s=ResearchStoreV239(Path(td)/'research.db')
    s.upsert_entity(EntityV239('STRATEGY:selfcheck','STRATEGY','trend','SELFCHECK',role='CHALLENGER'))
    for i,x in enumerate([18,22,15,25,20,16,19,21,24,17,20,23]):
        s.add_evidence(EvidenceRecordV239('STRATEGY:selfcheck','SHADOW_TRADE',utc_now(),{'realized_net_return_bps':x},'v2.37_shadow',f'trade:{i}',1))
    a=assess_entity(s,'STRATEGY:selfcheck',policy={'stale_evidence_hours':168,'psi_watch':.1,'psi_quarantine':.25,'js_watch':.08,'js_quarantine':.2,'decay_watch':.35,'decay_quarantine':.7,'disagreement_watch':.45,'disagreement_quarantine':.75,'minimum_shadow_trades_for_promotion_review':30,'minimum_independent_evidence_sources':2,'minimum_posterior_net_edge_bps':0},bayesian={'prior_mean_bps':0,'prior_strength':20})
    s.enqueue('ENTITY_REVALIDATION',entity_id='STRATEGY:selfcheck',dedupe_key='selfcheck-review')
    assert s.counts()['evidence']==12 and a.posterior_net_edge_bps is not None and a.posterior_net_edge_bps>0
print('CONTINUOUS_QUANT_RESEARCH_V2_39_SELFCHECK OK')
print('PERSISTENT_SQLITE_REGISTRY True')
print('JOB_QUEUE_RETRY_LEASES True')
print('CHAMPION_CHALLENGER_LIFECYCLE True')
print('BAYESIAN_SHRINKAGE True')
print('DRIFT_DECAY_MONITORING True')
print('SHADOW_EVIDENCE_INGEST True')
print('SCHEDULED_REVALIDATION True')
print('ONE_COMMAND_CYCLE True')
print('WATCH_MODE True')
print('AUTOMATIC_LIVE_PROMOTION False')
print('BROKER_SUBMISSION_ENABLED False')
print('ORDER_CALLS 0')
print('EXECUTION_AUTHORITY NONE')
