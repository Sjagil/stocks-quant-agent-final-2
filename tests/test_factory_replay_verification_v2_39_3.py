import json
from pathlib import Path
import pandas as pd
import pytest
import stocks.research.strategy_factory_1h as sf
import stocks.research.walkforward_splits as wf
from stocks.research.continuous.factory_oos_replay_v2_39_3 import replay_factory_oos


class Hyp:
    def __init__(self, hypothesis_id, strategy, family, horizon, params):
        self.hypothesis_id=hypothesis_id; self.strategy=strategy; self.family=family; self.horizon=horizon; self.params=params
class Spec:
    name='trend'


def _setup(monkeypatch,tmp_path,mismatch=False):
    root=tmp_path; art=root/'artifacts/research_runtime/strategy_factory_1h'; art.mkdir(parents=True)
    data=root/'a.parquet'; data.write_bytes(b'x')
    (art/'audit.json').write_text(json.dumps({'symbols':['AAPL'],'sources':{'AAPL':str(data)},'base_cost_bps_per_side':3,'fold_count':2,'anchor_symbol':'AAPL'}))
    pd.DataFrame([{'hypothesis_id':'h','fold':1,'test_trades':2,'test_net_expectancy_bps':999 if mismatch else 10.0,'test_profit_factor':2.0}]).to_csv(art/'fold_selected.csv',index=False)
    dates=pd.date_range('2025-01-01',periods=4000,freq='h',tz='UTC')
    frame=pd.DataFrame({'date':dates,'open':1.,'high':1.,'low':1.,'close':1.,'volume':1.})
    monkeypatch.setattr(pd,'read_parquet',lambda p: frame)
    monkeypatch.setattr(sf,'OneHourHypothesis',Hyp,raising=False)
    monkeypatch.setattr(sf,'eligible_1h_specs',lambda:[Spec()],raising=False)
    monkeypatch.setattr(sf,'prepare_one_hour_frame',lambda raw,symbol: raw.assign(symbol=symbol),raising=False)
    monkeypatch.setattr(sf,'build_feature_caches',lambda frames: {},raising=False)
    base=pd.Timestamp('2025-01-01T00:00:00Z')
    trades=pd.DataFrame([{'hypothesis_id':'h','strategy':'trend','family':'x','symbol':'AAPL','entry_time':base+pd.Timedelta(hours=10),'exit_time':base+pd.Timedelta(hours=11),'gross_return':.001,'score':1,'duration_bars':1,'forced':False},{'hypothesis_id':'h','strategy':'trend','family':'x','symbol':'AAPL','entry_time':base+pd.Timedelta(hours=20),'exit_time':base+pd.Timedelta(hours=21),'gross_return':.001,'score':1,'duration_bars':1,'forced':False}])
    monkeypatch.setattr(sf,'evaluate_hypothesis',lambda *a,**k: trades,raising=False)
    monkeypatch.setattr(sf,'contained_trades',lambda t,p: t.copy(),raising=False)
    monkeypatch.setattr(sf,'period_metrics',lambda t,p,cost_bps_per_side:{'trades':2,'net_expectancy_bps':10.0,'profit_factor':2.0},raising=False)
    monkeypatch.setattr(wf,'rolling_periods',lambda index,hold_bars,requested_folds:[{'train':['a','b'],'valid':['c','d'],'test':['e','f']},{'train':['a','b'],'valid':['c','d'],'test':['g','h']}],raising=False)
    return root


def test_replay_requires_summary_metric_match(monkeypatch,tmp_path):
    root=_setup(monkeypatch,tmp_path,False)
    entity={'entity_id':'STRATEGY:h','family':'x','metadata':{'strategy':'trend','family':'x','params_json':'{}','horizon':'1d'}}
    obs,prov=replay_factory_oos(root,entity,config={'artifact_root':'artifacts/research_runtime/strategy_factory_1h','replay_purge_bars':42,'require_selected_test_folds':True,'require_replay_metric_verification':True,'metric_abs_tolerance':1e-6,'metric_rel_tolerance':1e-5})
    assert len(obs)==2
    assert prov['replay_checks'][0]['passed']
    assert prov['selection_rule']=='TEST_OPENED_ONLY_AFTER_TRAIN_VALID_SELECTION'


def test_replay_fails_closed_when_reconstructed_fold_metrics_do_not_match(monkeypatch,tmp_path):
    root=_setup(monkeypatch,tmp_path,True)
    entity={'entity_id':'STRATEGY:h','family':'x','metadata':{'strategy':'trend','family':'x','params_json':'{}','horizon':'1d'}}
    with pytest.raises(RuntimeError,match='REPLAY_PROVENANCE_MISMATCH'):
        replay_factory_oos(root,entity,config={'artifact_root':'artifacts/research_runtime/strategy_factory_1h','replay_purge_bars':42,'require_selected_test_folds':True,'require_replay_metric_verification':True,'metric_abs_tolerance':1e-6,'metric_rel_tolerance':1e-5})
