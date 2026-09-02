import pandas as pd
import pytest
from stocks.research.continuous.oos_observation_validation_v2_39_3 import (
    effective_nonoverlap_observations, normalize_oos_observations,
)


def test_normalize_dedupes_and_clusters_overlap():
    base=pd.Timestamp('2025-01-01T00:00:00Z')
    rows=[
      {'hypothesis_id':'h','fold':1,'symbol':'aapl','entry_time':base,'exit_time':base+pd.Timedelta(hours=2),'gross_return':.01},
      {'hypothesis_id':'h','fold':1,'symbol':'msft','entry_time':base+pd.Timedelta(hours=1),'exit_time':base+pd.Timedelta(hours=3),'gross_return':.02},
      {'hypothesis_id':'h','fold':1,'symbol':'nvda','entry_time':base+pd.Timedelta(hours=4),'exit_time':base+pd.Timedelta(hours=5),'gross_return':.03},
    ]
    frame=normalize_oos_observations(pd.DataFrame(rows),entity_hypothesis_id='h')
    assert effective_nonoverlap_observations(frame)==2
    assert list(frame.symbol)==['AAPL','MSFT','NVDA']


def test_wrong_hypothesis_rejected():
    frame=pd.DataFrame([{'hypothesis_id':'other','fold':1,'symbol':'A','entry_time':'2025-01-01Z','exit_time':'2025-01-02Z','gross_return':.01}])
    with pytest.raises(ValueError,match='different hypothesis'):
        normalize_oos_observations(frame,entity_hypothesis_id='h')


def test_aggregate_summary_cannot_become_observation_evidence():
    frame=pd.DataFrame([{'hypothesis_id':'h','median_test_expectancy_bps':20,'test_trades':100}])
    with pytest.raises(ValueError,match='schema missing'):
        normalize_oos_observations(frame,entity_hypothesis_id='h')
