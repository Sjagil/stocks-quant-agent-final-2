import pandas as pd

from stocks.production.current_session_data_v2_41_2 import (
    closed_latest_session_bars,
    cross_provider_close_check,
    merge_overlay,
)


def frame(times, closes):
    return pd.DataFrame(
        {
            "open": closes,
            "high": [x + 1 for x in closes],
            "low": [x - 1 for x in closes],
            "close": closes,
            "volume": [1000] * len(times),
        },
        index=pd.to_datetime(times, utc=True),
    )


def test_cross_provider_overlap_passes_small_disagreement():
    times = [
        "2026-08-25 13:30:00+00:00",
        "2026-08-25 14:30:00+00:00",
        "2026-08-25 15:30:00+00:00",
    ]
    a = frame(times, [100, 101, 102])
    b = frame(times, [100.01, 101.01, 102.01])
    out = cross_provider_close_check(
        a, b, minimum_overlap_bars=3, maximum_close_disagreement_bps=50
    )
    assert out.passed
    assert out.overlap_bars == 3


def test_cross_provider_overlap_fails_large_disagreement():
    times = [
        "2026-08-25 13:30:00+00:00",
        "2026-08-25 14:30:00+00:00",
        "2026-08-25 15:30:00+00:00",
    ]
    a = frame(times, [100, 101, 102])
    b = frame(times, [110, 111, 112])
    out = cross_provider_close_check(
        a, b, minimum_overlap_bars=3, maximum_close_disagreement_bps=50
    )
    assert not out.passed
    assert out.reason == "CROSS_PROVIDER_CLOSE_DISAGREEMENT"


def test_only_closed_current_session_bars_survive():
    # 2026-08-26 is a normal NYSE session. At 19:03 UTC, a 17:30 start
    # has closed at 18:30, while 18:30 -> 19:30 is still incomplete.
    bars = frame(
        [
            "2026-08-26 13:30:00+00:00",
            "2026-08-26 14:30:00+00:00",
            "2026-08-26 15:30:00+00:00",
            "2026-08-26 16:30:00+00:00",
            "2026-08-26 17:30:00+00:00",
            "2026-08-26 18:30:00+00:00",
        ],
        [100, 101, 102, 103, 104, 105],
    )
    out, session = closed_latest_session_bars(
        bars,
        now=pd.Timestamp("2026-08-26 19:03:00+00:00"),
        calendar_name="NYSE",
        bar_period=pd.Timedelta(hours=1),
        close_lag=pd.Timedelta(minutes=2),
    )
    assert list(out.index) == list(bars.index[:5])
    assert session.market_open_now is True


def test_overlay_wins_duplicate_timestamp():
    hist = frame(["2026-08-25 13:30:00+00:00"], [100])
    over = frame(["2026-08-25 13:30:00+00:00"], [101])
    merged = merge_overlay(hist, over)
    assert len(merged) == 1
    assert float(merged.iloc[0]["close"]) == 101.0
