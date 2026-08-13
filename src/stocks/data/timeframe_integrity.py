from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pandas_market_calendars as mcal


INTRADAY_AVAILABILITY_MINUTES = {
    "15m": 15,
    "1h": 60,
    "2h": 15,
    "4h": 15,
}


@dataclass(frozen=True)
class AvailabilityFrame:
    timeframe: str
    frame: pd.DataFrame


def _utc_index(
    index: pd.Index,
) -> pd.DatetimeIndex:
    result = pd.DatetimeIndex(
        pd.to_datetime(
            index,
            utc=True,
        )
    )

    return result


def _nyse_schedule(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    calendar = mcal.get_calendar(
        "NYSE"
    )

    return calendar.schedule(
        start_date=(
            start.date()
        ),
        end_date=(
            end.date()
        ),
    )


def intraday_availability(
    frame: pd.DataFrame,
    *,
    timeframe: str,
) -> pd.DataFrame:
    if timeframe not in (
        INTRADAY_AVAILABILITY_MINUTES
    ):
        raise ValueError(
            f"unsupported intraday timeframe: "
            f"{timeframe}"
        )

    result = frame.copy()

    result.index = _utc_index(
        result.index
    )

    minutes = (
        INTRADAY_AVAILABILITY_MINUTES[
            timeframe
        ]
    )

    result[
        "bar_time"
    ] = result.index

    result[
        "availability_time"
    ] = (
        result.index
        + pd.Timedelta(
            minutes=minutes
        )
    )

    return result


def daily_availability(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result.index = _utc_index(
        result.index
    )

    schedule = _nyse_schedule(
        result.index.min()
        - pd.Timedelta(
            days=3
        ),
        result.index.max()
        + pd.Timedelta(
            days=3
        ),
    )

    closes_by_date = {
        pd.Timestamp(
            session_date
        ).date(): pd.Timestamp(
            row[
                "market_close"
            ]
        ).tz_convert(
            "UTC"
        )
        for session_date, row
        in schedule.iterrows()
    }

    availability = []

    for timestamp in result.index:
        local_date = (
            timestamp
            .tz_convert(
                "America/New_York"
            )
            .date()
        )

        close = closes_by_date.get(
            local_date
        )

        if close is None:
            raise ValueError(
                "no NYSE close for daily "
                f"bar {timestamp}"
            )

        availability.append(
            close
        )

    result[
        "bar_time"
    ] = result.index

    result[
        "availability_time"
    ] = pd.DatetimeIndex(
        availability
    )

    return result


def weekly_availability(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result.index = _utc_index(
        result.index
    )

    start = (
        result.index.min()
        - pd.Timedelta(
            days=7
        )
    )

    end = (
        result.index.max()
        + pd.Timedelta(
            days=10
        )
    )

    schedule = _nyse_schedule(
        start,
        end,
    )

    schedule = schedule.copy()

    local_dates = (
        schedule.index
        .to_period(
            "W-FRI"
        )
    )

    schedule[
        "_week"
    ] = local_dates.astype(
        str
    )

    weekly_close = (
        schedule.groupby(
            "_week"
        )[
            "market_close"
        ]
        .max()
    )

    availability = []

    for timestamp in result.index:
        local = (
            timestamp
            .tz_convert(
                "America/New_York"
            )
            .tz_localize(
                None
            )
        )

        period = local.to_period(
            "W-FRI"
        )

        key = str(
            period
        )

        if key not in weekly_close:
            raise ValueError(
                "no NYSE weekly close for "
                f"{timestamp}"
            )

        close = pd.Timestamp(
            weekly_close[
                key
            ]
        ).tz_convert(
            "UTC"
        )

        availability.append(
            close
        )

    result[
        "bar_time"
    ] = result.index

    result[
        "availability_time"
    ] = pd.DatetimeIndex(
        availability
    )

    return result


def with_availability(
    frame: pd.DataFrame,
    *,
    timeframe: str,
) -> pd.DataFrame:
    if timeframe in (
        INTRADAY_AVAILABILITY_MINUTES
    ):
        return intraday_availability(
            frame,
            timeframe=timeframe,
        )

    if timeframe == "1d":
        return daily_availability(
            frame
        )

    if timeframe == "1w":
        return weekly_availability(
            frame
        )

    raise ValueError(
        f"unsupported timeframe: "
        f"{timeframe}"
    )


def assert_no_future_availability(
    frame: pd.DataFrame,
) -> None:
    if "bar_time" not in frame:
        raise ValueError(
            "bar_time missing"
        )

    if (
        "availability_time"
        not in frame
    ):
        raise ValueError(
            "availability_time missing"
        )

    invalid = (
        frame[
            "availability_time"
        ]
        <
        frame[
            "bar_time"
        ]
    )

    if invalid.any():
        raise ValueError(
            "availability precedes bar time"
        )
