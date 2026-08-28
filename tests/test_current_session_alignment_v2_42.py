import pandas as pd
from stocks.production.current_session_alignment_v2_42 import align_ibkr_rth_to_eodhd_grid_v242


def test_ibkr_30m_aggregates_to_eodhd_half_hour_anchored_hourly_grid():
    idx = pd.date_range("2026-08-25 13:30:00+00:00", "2026-08-25 19:30:00+00:00", freq="30min")
    frame = pd.DataFrame({
        "open": range(100, 100 + len(idx)),
        "high": [x + 1 for x in range(100, 100 + len(idx))],
        "low": [x - 1 for x in range(100, 100 + len(idx))],
        "close": [x + 0.5 for x in range(100, 100 + len(idx))],
        "volume": [10.0] * len(idx),
    }, index=idx)
    aligned, audit = align_ibkr_rth_to_eodhd_grid_v242(
        frame, now=pd.Timestamp("2026-08-26 12:00:00+00:00"), close_lag_seconds=0
    )
    expected = pd.DatetimeIndex([
        "2026-08-25 13:30:00+00:00", "2026-08-25 14:30:00+00:00",
        "2026-08-25 15:30:00+00:00", "2026-08-25 16:30:00+00:00",
        "2026-08-25 17:30:00+00:00", "2026-08-25 18:30:00+00:00",
        "2026-08-25 19:30:00+00:00",
    ], name="timestamp")
    assert aligned.index.equals(expected)
    assert aligned.iloc[0]["open"] == 100
    assert aligned.iloc[0]["close"] == 101.5
    assert aligned.iloc[0]["volume"] == 20
    assert aligned.iloc[-1]["volume"] == 10
    assert audit.aligned_rows == 7


def test_forming_target_bucket_is_not_admitted():
    idx = pd.DatetimeIndex(["2026-08-26 13:30:00+00:00", "2026-08-26 14:00:00+00:00", "2026-08-26 14:30:00+00:00"])
    frame = pd.DataFrame({"open":[1,2,3],"high":[2,3,4],"low":[.5,1,2],"close":[1.5,2.5,3.5],"volume":[10,10,10]}, index=idx)
    aligned, _ = align_ibkr_rth_to_eodhd_grid_v242(frame, now=pd.Timestamp("2026-08-26 14:45:00+00:00"), close_lag_seconds=120)
    assert list(aligned.index) == [pd.Timestamp("2026-08-26 13:30:00+00:00")]
