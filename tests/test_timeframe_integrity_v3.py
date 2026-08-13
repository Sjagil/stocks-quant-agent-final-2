import pandas as pd

from stocks.data.timeframe_integrity import (
    assert_no_future_availability,
    with_availability,
)
from stocks.data.timeframe_pipeline import (
    rolling_intraday_context,
)


def test_15m_available_only_after_close():
    index = pd.DatetimeIndex(
        [
            "2026-01-05 14:30:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
        },
        index=index,
    )

    result = with_availability(
        frame,
        timeframe="15m",
    )

    assert (
        result[
            "availability_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2026-01-05 14:45:00+00:00"
        )
    )


def test_1h_available_only_after_close():
    index = pd.DatetimeIndex(
        [
            "2026-01-05 14:30:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
        },
        index=index,
    )

    result = with_availability(
        frame,
        timeframe="1h",
    )

    assert (
        result[
            "availability_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2026-01-05 15:30:00+00:00"
        )
    )


def test_daily_bar_is_not_available_at_midnight():
    index = pd.DatetimeIndex(
        [
            "2026-01-05 05:00:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
        },
        index=index,
    )

    result = with_availability(
        frame,
        timeframe="1d",
    )

    assert (
        result[
            "availability_time"
        ].iloc[0]
        >
        result[
            "bar_time"
        ].iloc[0]
    )

    assert_no_future_availability(
        result
    )


def test_rolling_context_restarts_after_gap():
    index = pd.date_range(
        "2026-01-05 14:30",
        periods=20,
        freq="15min",
        tz="UTC",
    )

    index = index.delete(
        8
    )

    values = [
        100.0 + i
        for i in range(
            len(index)
        )
    ]

    frame = pd.DataFrame(
        {
            "open": values,
            "high": [
                value + 1.0
                for value in values
            ],
            "low": [
                value - 1.0
                for value in values
            ],
            "close": [
                value + 0.5
                for value in values
            ],
            "volume": 1000.0,
        },
        index=index,
    )

    result = (
        rolling_intraday_context(
            frame,
            window_bars=8,
        )
    )

    gap_time = pd.Timestamp(
        "2026-01-05 16:30:00+00:00"
    )

    assert (
        gap_time not in result.index
    )


def test_final_1h_bar_is_available_at_market_close():
    index = pd.DatetimeIndex(
        [
            "2026-01-05 20:30:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [1000.0],
        },
        index=index,
    )

    result = with_availability(
        frame,
        timeframe="1h",
    )

    assert (
        result[
            "availability_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2026-01-05 21:00:00+00:00"
        )
    )


def test_early_close_drops_bar_starting_at_market_close():
    index = pd.DatetimeIndex(
        [
            "2024-11-29 17:30:00+00:00",
            "2024-11-29 18:00:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
            ],
            "high": [
                101.0,
                102.0,
            ],
            "low": [
                99.0,
                100.0,
            ],
            "close": [
                100.5,
                101.5,
            ],
            "volume": [
                1000.0,
                1100.0,
            ],
        },
        index=index,
    )

    result = with_availability(
        frame,
        timeframe="1h",
    )

    assert len(result) == 1

    assert (
        result[
            "bar_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2024-11-29 17:30:00+00:00"
        )
    )

    assert (
        result[
            "availability_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2024-11-29 18:00:00+00:00"
        )
    )
