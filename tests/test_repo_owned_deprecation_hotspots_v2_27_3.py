from __future__ import annotations

from pathlib import Path


HOTSPOTS = {
    "src/stocks/research/market_structure_15m_execution.py": (
        "pd.Timedelta(\\n    minutes=15",
        "pd.Timedelta(\\n    hours=1",
    ),
    "src/stocks/data/eodhd_daily_source.py": (
        "pd.Timedelta(hours=16)",
    ),
    "src/stocks/data/eodhd_5m_source.py": (
        "pd.Timedelta(\\n                        minutes=5",
        "pd.Timedelta(\\n                        minutes=10",
    ),
    "src/stocks/providers/eodhd.py": (
        "pd.Timedelta(\\n        days=int(chunk_days)",
    ),
    "src/stocks/research/eodhd_holdout_hydration.py": (
        'pd.Timedelta("1D")',
        'pd.Timedelta("1us")',
        'pd.Timedelta("10D")',
        'pd.Timedelta("1h")',
    ),
    "src/stocks/data/current_session_bridge_v2_27.py": (
        'pd.Timedelta("14D")',
        'pd.Timedelta("10D")',
        'pd.Timedelta("1D")',
        'pd.Timedelta("1h")',
        'pd.Timedelta("30min")',
    ),
    "src/stocks/data/timeframe_integrity.py": (
        "pd.Timedelta(\\n            days=3",
        "pd.Timedelta(\\n                minutes=minutes",
        "pd.Timedelta(\\n            days=7",
        "pd.Timedelta(\\n            days=10",
    ),
    "src/stocks/research/pit_shariah_eligibility_v2_25.py": (
        "pd.Timedelta(days=int(lag_days))",
    ),
    "src/stocks/data/reference_15m_intake.py": (
        "pd.Timedelta(\\n        minutes=15",
    ),
    "src/stocks/data/session_hourly.py": (
        "pd.Timedelta(\\n        minutes=15",
        "pd.Timedelta(\\n        hours=1",
    ),
    "src/stocks/orchestration/start_preflight_v2_26.py": (
        "pd.Timedelta(days=10)",
        "pd.Timedelta(hours=1)",
    ),
    "src/stocks/data/timeframe_pipeline.py": (
        "pd.Timedelta(\\n            minutes=15",
    ),
}


def test_known_repo_owned_timedelta_warning_hotspots_removed():
    for rel, forbidden in HOTSPOTS.items():
        text = Path(rel).read_text(encoding="utf-8")
        for value in forbidden:
            assert value not in text, f"{rel}: {value}"
