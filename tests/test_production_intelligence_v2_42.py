import pandas as pd
from stocks.production.intelligence_v2_42 import macro_context_v242, apply_production_context_v242

CFG = {
    "macro": {
        "high_impact_pre_minutes": 90, "high_impact_post_minutes": 30,
        "medium_impact_pre_minutes": 60, "medium_conviction_multiplier": 0.85,
        "high_impact_keywords": ["cpi", "fomc"], "medium_impact_keywords": ["pmi"],
    }
}


def test_future_high_impact_macro_blocks_without_using_actual():
    now = pd.Timestamp("2026-08-26 12:00:00+00:00")
    events = [{"type":"CPI Inflation Rate", "event_time":"2026-08-26T13:00:00+00:00", "actual":999, "estimate":2.5}]
    ctx = macro_context_v242(events, now=now, cfg=CFG)
    assert "MACRO_HIGH_IMPACT_WINDOW" in ctx["blockers"]
    assert ctx["events"][0]["actual"] is None


def test_context_cannot_originate_trade_but_can_block_existing_buy():
    proposals = pd.DataFrame([{"symbol":"AAPL","decision":"BUY_NEW","conviction":0.8,"blockers":""}])
    macro = {"blockers":["MACRO_HIGH_IMPACT_WINDOW"], "conviction_multiplier":1.0, "high_impact_window":True}
    news = {"AAPL":{"weighted_sentiment":-0.7,"conviction_multiplier":0.8,"blockers":["NEGATIVE_NEWS_RISK"],"nlp_backend":"transformers","stories_evidence":3}}
    out = apply_production_context_v242(proposals, macro=macro, news_by_symbol=news, generated_at=pd.Timestamp("2026-08-26T12:00:00Z"))
    assert out.iloc[0]["decision"] == "BUY_NEW"
    assert "MACRO_HIGH_IMPACT_WINDOW" in out.iloc[0]["blockers"]
    assert "NEGATIVE_NEWS_RISK" in out.iloc[0]["blockers"]
    assert float(out.iloc[0]["conviction"]) < 0.8
