import json
from pathlib import Path
import pandas as pd
from stocks.research.continuous.factory_oos_replay_v2_39_3 import audit_factory_replay_inputs


def _project(tmp_path,with_selected=True):
    root=tmp_path
    a=root/'artifacts/research_runtime/strategy_factory_1h'; a.mkdir(parents=True)
    data=root/'data.parquet'; data.write_bytes(b'x')
    (a/'audit.json').write_text(json.dumps({'symbols':['AAPL'],'sources':{'AAPL':str(data)},'base_cost_bps_per_side':3,'fold_count':4}))
    pd.DataFrame(([{'hypothesis_id':'h','fold':1}] if with_selected else [{'hypothesis_id':'z','fold':1}])).to_csv(a/'fold_selected.csv',index=False)
    return root


def test_factory_input_audit_ready_when_selection_and_sources_exist(tmp_path):
    root=_project(tmp_path)
    entity={'entity_id':'STRATEGY:h','metadata':{'strategy':'trend','params_json':'{}'}}
    a=audit_factory_replay_inputs(root,entity,config={'artifact_root':'artifacts/research_runtime/strategy_factory_1h','require_selected_test_folds':True,'replay_purge_bars':42})
    assert a.ready
    assert a.details['selected_folds']==[1]


def test_factory_input_audit_blocks_missing_selected_provenance(tmp_path):
    root=_project(tmp_path,False)
    entity={'entity_id':'STRATEGY:h','metadata':{'strategy':'trend','params_json':'{}'}}
    a=audit_factory_replay_inputs(root,entity,config={'artifact_root':'artifacts/research_runtime/strategy_factory_1h','require_selected_test_folds':True})
    assert not a.ready
    assert 'NO_SELECTED_TEST_FOLDS' in a.reasons
