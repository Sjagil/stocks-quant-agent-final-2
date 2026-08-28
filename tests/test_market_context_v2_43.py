import json
from datetime import timedelta

import pandas as pd

from stocks.news.contracts import RawNewsItem
from stocks.news.dedup import cluster_news
from stocks.production.context_v2_43 import (
    apply_context_policy_v243,
    build_snapshot_v243,
    normalize_economic_event_v243,
    verify_snapshot_v243,
)


def _cfg():
    return json.loads(open("config/market_context_v2_43.json", encoding="utf-8").read())


def _snapshot(calendar=None, news=None):
    return build_snapshot_v243(
        decision_cutoff="2026-08-28T14:00:00Z",
        symbols=["SPY", "QQQ", "AAPL"],
        market_regime={"label": "NEUTRAL"},
        calendar_context=calendar or {
            "status": "FRESH",
            "entry_blockers": [],
            "calendar_adjustment": 0.0,
        },
        news_context=news or {
            "AAPL": {
                "critical_context_available": True,
                "news_present": False,
                "finbert_ready": True,
                "negative_tail_score": 0.0,
                "event_risk_score": 0.0,
                "sentiment_6h": 0.0,
            }
        },
        data_freshness=[
            {"symbol": "SPY", "status": "FRESH"},
            {"symbol": "QQQ", "status": "FRESH"},
        ],
        provider_provenance=[],
    ).to_dict()


def test_future_economic_actual_is_never_visible():
    event = normalize_economic_event_v243(
        {
            "id": "CPI",
            "type": "CPI",
            "country": "US",
            "date": "2026-08-28T13:30:00Z",
            "published_at": "2026-08-28T14:01:00Z",
            "forecast": 2.8,
            "actual": 3.1,
        },
        decision_cutoff="2026-08-28T14:00:00Z",
        cfg=_cfg(),
    )
    assert event.actual is None
    assert event.revision is None
    assert event.surprise is None


def test_actual_without_explicit_published_at_is_fail_closed():
    event = normalize_economic_event_v243(
        {
            "id": "CPI",
            "type": "CPI",
            "country": "US",
            "date": "2026-08-28T13:30:00Z",
            "forecast": 2.8,
            "actual": 3.1,
        },
        decision_cutoff="2026-08-28T14:00:00Z",
        cfg=_cfg(),
    )
    assert event.actual is None
    assert event.release_visibility == "UNVERIFIED_RELEASE_TIME"


def test_snapshot_is_content_addressed_and_verifiable():
    snapshot = _snapshot()
    assert snapshot["snapshot_id"].startswith("CTX-")
    assert verify_snapshot_v243(snapshot)


def test_context_never_creates_new_entry():
    proposals = pd.DataFrame([{
        "symbol": "AAPL",
        "decision": "SKIP",
        "conviction": 0.95,
        "blockers": "",
    }])
    out = apply_context_policy_v243(
        proposals,
        snapshot=_snapshot(news={
            "AAPL": {
                "critical_context_available": True,
                "news_present": True,
                "finbert_ready": True,
                "negative_tail_score": 0.0,
                "event_risk_score": 0.0,
                "sentiment_6h": 1.0,
            }
        }),
        cfg=_cfg(),
        now="2026-08-28T14:00:00Z",
    )
    assert out.iloc[0]["decision_before_context"] == "SKIP"
    assert out.iloc[0]["decision_after_context"] == "SKIP"


def test_high_impact_context_changes_buy_to_skip_with_audit():
    proposals = pd.DataFrame([{
        "symbol": "AAPL",
        "decision": "BUY_NEW",
        "conviction": 0.84,
        "blockers": "",
    }])
    out = apply_context_policy_v243(
        proposals,
        snapshot=_snapshot(calendar={
            "status": "FRESH",
            "entry_blockers": ["FOMC_WINDOW"],
            "calendar_adjustment": -0.20,
        }),
        cfg=_cfg(),
        now="2026-08-28T14:00:00Z",
    )
    row = out.iloc[0]
    assert row["raw_conviction"] == 0.84
    assert row["calendar_adjustment"] == -0.20
    assert row["decision_before_context"] == "BUY_NEW"
    assert row["decision_after_context"] == "SKIP"
    assert "FOMC_WINDOW" in row["context_blockers"]


def test_duplicate_syndication_is_one_story_cluster():
    now = pd.Timestamp("2026-08-28T14:00:00Z").to_pydatetime()
    rows = [
        RawNewsItem(
            "eodhd", "1", now - timedelta(minutes=5),
            "Company cuts guidance after weak demand", "https://a",
            symbols=("AAPL",),
        ),
        RawNewsItem(
            "yfinance", "2", now - timedelta(minutes=4),
            "Company cuts guidance after weak demand", "https://b",
            symbols=("AAPL",),
        ),
    ]
    assert len(cluster_news(rows)) == 1
