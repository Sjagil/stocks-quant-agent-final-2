from datetime import date

import pandas as pd

from stocks.research.market_structure_15m_execution import (
    complete_hour_bars,
    first_limit_fill,
    first_stop_fill,
    full_history_eligibility,
)


def bars(
    timestamps,
    *,
    opens,
    highs,
    lows,
    closes,
):
    return pd.DataFrame(
        {
            "symbol": [
                "TEST"
            ]
            * len(
                timestamps
            ),
            "date": pd.to_datetime(
                timestamps,
                utc=True,
            ),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [
                1000.0
            ]
            * len(
                timestamps
            ),
        }
    )


def test_limit_fill_uses_first_touch(
):
    frame = bars(
        [
            "2026-01-05 14:30:00+00:00",
            "2026-01-05 14:45:00+00:00",
        ],
        opens=[
            101.0,
            99.0,
        ],
        highs=[
            102.0,
            101.0,
        ],
        lows=[
            100.5,
            97.0,
        ],
        closes=[
            101.5,
            100.0,
        ],
    )

    fill = first_limit_fill(
        frame,
        level=100.0,
    )

    assert fill is not None

    assert (
        fill["time"]
        == pd.Timestamp(
            "2026-01-05 "
            "14:45:00+00:00"
        )
    )

    assert (
        fill["price"]
        == 99.0
    )

    assert (
        fill["gap_fill"]
        is True
    )


def test_same_15m_stop_occurs_after_fill(
):
    frame = bars(
        [
            "2026-01-05 14:30:00+00:00",
        ],
        opens=[
            101.0,
        ],
        highs=[
            102.0,
        ],
        lows=[
            95.0,
        ],
        closes=[
            99.0,
        ],
    )

    fill = first_limit_fill(
        frame,
        level=100.0,
    )

    assert fill is not None

    stop = first_stop_fill(
        frame,
        stop_price=98.0,
        not_before=fill[
            "time"
        ],
    )

    assert stop is not None

    assert (
        stop["time"]
        == fill["time"]
    )

    assert (
        stop["price"]
        == 98.0
    )


def test_missing_subbar_fails_hour_completeness(
):
    frame = bars(
        [
            "2026-01-05 14:30:00+00:00",
            "2026-01-05 14:45:00+00:00",
            "2026-01-05 15:15:00+00:00",
        ],
        opens=[
            100.0,
            100.0,
            100.0,
        ],
        highs=[
            101.0,
            101.0,
            101.0,
        ],
        lows=[
            99.0,
            99.0,
            99.0,
        ],
        closes=[
            100.0,
            100.0,
            100.0,
        ],
    )

    bounds = {
        date(
            2026,
            1,
            5,
        ): (
            pd.Timestamp(
                "2026-01-05 "
                "14:30:00+00:00"
            ),
            pd.Timestamp(
                "2026-01-05 "
                "21:00:00+00:00"
            ),
        )
    }

    result, missing = (
        complete_hour_bars(
            frame,
            pd.Timestamp(
                "2026-01-05 "
                "14:30:00+00:00"
            ),
            bounds,
        )
    )

    assert result.empty

    assert list(
        missing
    ) == [
        pd.Timestamp(
            "2026-01-05 "
            "15:00:00+00:00"
        )
    ]


def test_late_15m_history_is_not_full_history(
):
    one_hour = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    (
                        "2020-10-12 "
                        "13:30:00+00:00"
                    ),
                    (
                        "2026-08-13 "
                        "19:30:00+00:00"
                    ),
                ],
                utc=True,
            )
        }
    )

    fifteen = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    (
                        "2026-04-15 "
                        "13:30:00+00:00"
                    ),
                    (
                        "2026-08-13 "
                        "19:45:00+00:00"
                    ),
                ],
                utc=True,
            )
        }
    )

    result = (
        full_history_eligibility(
            one_hour,
            fifteen,
        )
    )

    assert (
        result[
            "eligible"
        ]
        is False
    )
