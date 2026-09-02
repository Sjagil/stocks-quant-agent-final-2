from stocks.research.continuous.contracts_v2_39 import EntityV239
from stocks.research.continuous.evidence_production_ingest_v2_39_3 import ingest_produced_evidence
from stocks.research.continuous.evidence_taxonomy_v2_39_2 import evidence_breadth_v2392
from stocks.research.continuous.store_v2_39 import ResearchStoreV239


def test_oos_and_execution_cost_are_two_promotion_sources(tmp_path):
    s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('STRATEGY:h','STRATEGY'))
    rows=[{'stress_multiplier':m,'expectancy_bps':10,'net_edge_bps':10,'passed':True,'effective_observations':80} for m in (1,1.5,2,3)]
    out=ingest_produced_evidence(s,entity_id='STRATEGY:h',oos_metrics={'observations':80,'net_edge_bps':12,'passed':True},cost_rows=rows,oos_source_ref='oos-x',cost_source_prefix='cost-x',as_of='2026-08-20T00:00:00+00:00')
    assert out['added']==5
    breadth=evidence_breadth_v2392(s.evidence_for('STRATEGY:h'),fresh_hours=720)
    assert set(breadth.promotion_classes)=={'COST_ROBUSTNESS','OOS_VALIDATION'}
    assert len(breadth.promotion_sources)==2


def test_ingest_is_idempotent_for_same_provenance(tmp_path):
    s=ResearchStoreV239(tmp_path/'r.db'); s.upsert_entity(EntityV239('STRATEGY:h','STRATEGY'))
    rows=[{'stress_multiplier':2.0,'expectancy_bps':10,'net_edge_bps':10,'passed':True,'effective_observations':80}]
    a=ingest_produced_evidence(s,entity_id='STRATEGY:h',oos_metrics={'observations':80,'net_edge_bps':12,'passed':True},cost_rows=rows,oos_source_ref='oos-x',cost_source_prefix='cost-x',as_of='2026-08-20T00:00:00+00:00')
    b=ingest_produced_evidence(s,entity_id='STRATEGY:h',oos_metrics={'observations':80,'net_edge_bps':12,'passed':True},cost_rows=rows,oos_source_ref='oos-x',cost_source_prefix='cost-x',as_of='2026-08-20T00:00:00+00:00')
    assert a['added']==2 and b['added']==0
