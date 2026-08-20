from __future__ import annotations

import pandas as pd

from stocks.data.eodhd_daily_source import normalize_eodhd_daily


def test_daily_normalizer_uses_exchange_session_close():
    payload = [
        {
            "date": "2026-01-05",
            "open": 100.0,
            "high": 103.0,
            "low": 99.0,
            "close": 102.0,
            "adjusted_close": 102.0,
            "volume": 1000,
        }
    ]
    frame = normalize_eodhd_daily(payload)
    assert len(frame) == 1
    # January NYSE close is 21:00 UTC.
    assert frame.index[0].hour == 21
    assert frame.index[0].date().isoformat() == "2026-01-05"


def test_daily_normalizer_rejects_missing_ohlcv():
    payload = [{"date": "2026-01-05", "close": 100.0}]
    try:
        normalize_eodhd_daily(payload)
    except ValueError as exc:
        assert "missing fields" in str(exc)
    else:
        raise AssertionError("expected ValueError")
