import json
import pandas as pd
import pytest
from stocks.research.continuous.external_oos_evidence_v2_39_3 import load_external_observations,validate_external_provenance


def test_external_provenance_must_prove_test_labels_were_not_used():
    with pytest.raises(ValueError,match='selected_without_test_labels'):
        validate_external_provenance({'selection_protocol':'PURGED_WALK_FORWARD','selected_without_test_labels':False,'label_overlap_checked':True,'source_engine':'x','data_as_of':'2026-08-01T00:00:00Z'})


def test_external_observation_file_gets_content_bound_provenance(tmp_path):
    obs=tmp_path/'obs.csv'; prov=tmp_path/'prov.json'
    pd.DataFrame([{'hypothesis_id':'h','fold':1,'symbol':'AAPL','entry_time':'2026-08-01T00:00:00Z','exit_time':'2026-08-01T01:00:00Z','gross_return':.01}]).to_csv(obs,index=False)
    prov.write_text(json.dumps({'selection_protocol':'PURGED_WALK_FORWARD','selected_without_test_labels':True,'label_overlap_checked':True,'source_engine':'external_engine','data_as_of':'2026-08-01T01:00:00Z'}))
    frame,p=load_external_observations(obs,prov,entity_hypothesis_id='h')
    assert len(frame)==1
    assert len(p['observations_sha256'])==64
    assert len(p['provenance_hash'])==64
