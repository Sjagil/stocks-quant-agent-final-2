import numpy as np
import pandas as pd

from stocks.data.multitimeframe import (
    aggregate_bars,
    build_active_swing_bundle,
)


def hourly_frame(rows: int = 400) -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-02 14:30",
        periods=rows,
        freq="h",
        tz="UTC",
    )

    close = 100 + np.linspace(0, 20, rows)

    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(rows, 1000.0),
        },
        index=index,
    )


def test_1h_can_causally_aggregate_to_2h_and_4h() -> None:
    frame = hourly_frame()

    two_hour = aggregate_bars(
        frame,
        source_timeframe="1h",
        target_timeframe="2h",
    )

    four_hour = aggregate_bars(
        frame,
        source_timeframe="1h",
        target_timeframe="4h",
    )

    assert not two_hour.empty
    assert not four_hour.empty
    assert len(four_hour) < len(two_hour) < len(frame)


def test_active_bundle_never_invents_15m() -> None:
    frame = hourly_frame()

    bundle = build_active_swing_bundle(
        "TEST",
        {"1h": frame},
    )

    assert "1h" in bundle.frames
    assert "2h" in bundle.frames
    assert "4h" in bundle.frames
    assert "15m" not in bundle.frames


def test_5m_can_causally_aggregate_to_15m() -> None:
    index = pd.date_range(
        "2026-01-05 14:30",
        periods=300,
        freq="5min",
        tz="UTC",
    )

    close = (
        100
        + np.linspace(
            0,
            5,
            len(index),
        )
    )

    frame = pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": np.full(
                len(index),
                1000.0,
            ),
        },
        index=index,
    )

    result = aggregate_bars(
        frame,
        source_timeframe="5m",
        target_timeframe="15m",
    )

    assert not result.empty

    assert len(result) <= (
        len(frame) // 3
    )
