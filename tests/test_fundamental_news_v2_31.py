from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from stocks.research.fundamental_features_v2_31 import build_fundamental_raw_features, score_fundamental_panel
from stocks.research.news_features_v2_31 import NewsEvent, aggregate_news_features, event_decay


def _fund_frame():
    rows=[]
    for date in (1,2):
        for i,s in enumerate(("A","B","C","D"),1):
            rows.append({"date":date,"symbol":s,"nopat":10*i,"invested_capital":100,"free_cash_flow":8*i,"revenue":100,"gross_profit":30+2*i,"net_income":7*i,"average_assets":120,"market_cap":200+10*i,"ebitda":12*i,"net_debt":20,"ebit":10*i,"interest_expense":2,"actual_eps":1.0+0.1*i,"consensus_eps":1.0,"eps_estimate":1.0+0.05*i,"eps_estimate_prior":1.0,"revenue_prior":95,"eps":1.1*i,"eps_prior":1.0*i,"free_cash_flow_prior":7*i,"gross_margin_prior":0.30})
    return pd.DataFrame(rows)


def test_fundamental_ratios_and_composites_are_finite():
    frame=_fund_frame()
    raw=build_fundamental_raw_features(frame)
    assert np.isfinite(raw["roic"]).all()
    scored=score_fundamental_panel(frame,date_column="date")
    assert scored["fundamental_composite_score"].notna().all()
    assert scored.loc[3,"fundamental_revision_score"] > scored.loc[0,"fundamental_revision_score"]


def test_news_decay_duplicate_penalty_and_future_filter():
    now=datetime(2026,1,10,tzinfo=timezone.utc)
    assert abs(event_decay(24,half_life_hours=24)-0.5) < 1e-12
    events=[
        NewsEvent("A",now-timedelta(hours=2),0.8,source="r1",event_class="earnings",cluster_id="same"),
        NewsEvent("A",now-timedelta(hours=2),0.8,source="copy",event_class="earnings",cluster_id="same"),
        NewsEvent("A",now-timedelta(hours=1),-0.2,source="r2",event_class="analyst",cluster_id="independent"),
        NewsEvent("A",now+timedelta(hours=1),1.0,source="future",event_class="earnings"),
    ]
    out=aggregate_news_features(events,asof=now).iloc[0]
    assert out["news_event_count"] == 3
    assert out["news_independent_clusters"] == 2
    assert -1 <= out["news_weighted_sentiment"] <= 1
