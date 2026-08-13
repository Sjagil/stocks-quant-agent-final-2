import pandas as pd

from stocks.data.session_hourly import (
    aggregate_session_hourly,
)


def full_winter_session():
    index = pd.date_range(
        "2026-01-05 14:30:00+00:00",
        "2026-01-05 20:45:00+00:00",
        freq="15min",
    )

    values = [
        100.0 + i
        for i in range(
            len(index)
        )
    ]

    return pd.DataFrame(
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


def test_hourly_session_keeps_final_half_hour():
    result, audit = (
        aggregate_session_hourly(
            full_winter_session(),
            as_of=(
                "2026-01-05 "
                "21:00:00+00:00"
            ),
        )
    )

    assert len(result) == 7

    assert (
        result.index[-1]
        ==
        pd.Timestamp(
            "2026-01-05 "
            "20:30:00+00:00"
        )
    )

    assert (
        audit["coverage"]
        == 1.0
    )


def test_hourly_does_not_publish_open_bucket():
    frame = full_winter_session()

    result, _ = (
        aggregate_session_hourly(
            frame,
            as_of=(
                "2026-01-05 "
                "18:03:00+00:00"
            ),
        )
    )

    assert (
        result.index[-1]
        ==
        pd.Timestamp(
            "2026-01-05 "
            "16:30:00+00:00"
        )
    )
