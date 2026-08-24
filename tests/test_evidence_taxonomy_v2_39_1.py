from stocks.research.continuous.evidence_taxonomy_v2_39_1 import *
def test_registry_snapshot_is_metadata_not_independent():
 assert evidence_class('REGISTRY_SNAPSHOT')==UPSTREAM_METADATA and UPSTREAM_METADATA not in INDEPENDENT_OUTCOME_CLASSES
def test_source_groups_coarsen_correlated_evidence():
 assert source_group({'source':'v2.37_shadow_a'})==source_group({'source':'v2.37_shadow_b'})=='shadow_v237'
