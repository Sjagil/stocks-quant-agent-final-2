import numpy as np
import pandas as pd

from stocks.data.timeframe_pipeline import (
    rolling_intraday_context,
)


def rth_15m_frame(
    days: tuple[str, ...] = (
        "2026-01-05",
        "2026-01-06",
    ),
) -> pd.DataFrame:
    indices = []

    for day in days:
        local = pd.date_range(
            f"{day} 09:30",
            f"{day} 15:45",
            freq="15min",
            tz="America/New_York",
        )

        indices.append(
            local.tz_convert(
                "UTC"
            )
        )

    index = indices[0]

    for extra in indices[1:]:
        index = index.append(
            extra
        )

    values = (
        100.0
        + np.arange(
            len(index),
            dtype=float,
        )
        * 0.1
    )

    return pd.DataFrame(
        {
            "open": values,
            "high": values + 0.2,
            "low": values - 0.2,
            "close": values + 0.1,
            "volume": np.full(
                len(index),
                1000.0,
            ),
        },
        index=index,
    )


def test_full_rth_session_has_26_15m_bars():
    frame = rth_15m_frame(
        (
            "2026-01-05",
        )
    )

    assert len(frame) == 26


def test_2h_context_keeps_session_close():
    frame = rth_15m_frame()

    result = (
        rolling_intraday_context(
            frame,
            window_bars=8,
        )
    )

    assert len(result) == (
        2 * (26 - 8 + 1)
    )

    for day in (
        "2026-01-05",
        "2026-01-06",
    ):
        source_day = frame.loc[
            frame.index
            .tz_convert(
                "America/New_York"
            )
            .date
            == pd.Timestamp(
                day
            ).date()
        ]

        result_day = result.loc[
            result.index
            .tz_convert(
                "America/New_York"
            )
            .date
            == pd.Timestamp(
                day
            ).date()
        ]

        assert (
            result_day.index[-1]
            == source_day.index[-1]
        )


def test_4h_context_keeps_session_close():
    frame = rth_15m_frame()

    result = (
        rolling_intraday_context(
            frame,
            window_bars=16,
        )
    )

    assert len(result) == (
        2 * (26 - 16 + 1)
    )

    for day in (
        "2026-01-05",
        "2026-01-06",
    ):
        source_day = frame.loc[
            frame.index
            .tz_convert(
                "America/New_York"
            )
            .date
            == pd.Timestamp(
                day
            ).date()
        ]

        result_day = result.loc[
            result.index
            .tz_convert(
                "America/New_York"
            )
            .date
            == pd.Timestamp(
                day
            ).date()
        ]

        assert (
            result_day.index[-1]
            == source_day.index[-1]
        )


def test_context_never_crosses_overnight():
    frame = rth_15m_frame()

    two_hour = (
        rolling_intraday_context(
            frame,
            window_bars=8,
        )
    )

    four_hour = (
        rolling_intraday_context(
            frame,
            window_bars=16,
        )
    )

    assert len(two_hour) == 38
    assert len(four_hour) == 22
