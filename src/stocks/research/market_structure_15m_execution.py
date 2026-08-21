from __future__ import annotations

from datetime import timedelta

import math
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import canonicalize_ohlcv
from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
)
from stocks.research.strategy_factory_1h import (
    prepare_one_hour_frame,
)


FIFTEEN_MINUTES = timedelta(minutes=15)

ONE_HOUR = timedelta(hours=1)


def utc_timestamp(
    value,
) -> pd.Timestamp:
    result = pd.Timestamp(
        value
    )

    if result.tzinfo is None:
        return result.tz_localize(
            "UTC"
        )

    return result.tz_convert(
        "UTC"
    )


def one_hour_source(
    root: Path,
    symbol: str,
) -> Path:
    symbol = symbol.upper()

    candidates = (
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_1h.parquet",
        root
        / "data"
        / "adjusted"
        / f"{symbol}_1h.parquet",
        root
        / "data"
        / "derived"
        / f"{symbol}_1h.parquet",
        root
        / "data"
        / "processed"
        / f"{symbol}_1h.parquet",
    )

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        f"{symbol}: 1h source missing"
    )


def fifteen_minute_source(
    root: Path,
    symbol: str,
) -> Path:
    symbol = symbol.upper()

    candidates = (
        root
        / "data"
        / "canonical"
        / "split_adjusted"
        / f"{symbol}_15m.parquet",
        root
        / "data"
        / "canonical"
        / "provider_fabric"
        / f"{symbol}_15m.parquet",
    )

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        f"{symbol}: 15m source missing"
    )


def prepare_fifteen_minute_frame(
    frame: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    work = (
        canonicalize_ohlcv(
            frame
        )
        .reset_index()
    )

    time_column = None

    for candidate in (
        "timestamp",
        "datetime",
        "date",
        "timestamp_utc",
    ):
        if candidate in work.columns:
            time_column = candidate
            break

    if time_column is None:
        raise ValueError(
            f"{symbol}: 15m timestamp missing"
        )

    work = work.rename(
        columns={
            time_column: "date"
        }
    )

    work["date"] = pd.to_datetime(
        work["date"],
        utc=True,
        errors="coerce",
    )

    work = (
        work.dropna(
            subset=[
                "date",
                "open",
                "high",
                "low",
                "close",
            ]
        )
        .sort_values(
            "date"
        )
        .drop_duplicates(
            "date",
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    if work["date"].duplicated().any():
        raise ValueError(
            f"{symbol}: duplicate 15m timestamps"
        )

    work["symbol"] = (
        symbol.upper()
    )

    if "volume" not in work.columns:
        work["volume"] = np.nan

    return work[
        [
            "symbol",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].copy()


def load_symbol_frames(
    root: Path,
    symbol: str,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    Path,
    Path,
]:
    one_path = one_hour_source(
        root,
        symbol,
    )

    fifteen_path = fifteen_minute_source(
        root,
        symbol,
    )

    one_hour = prepare_one_hour_frame(
        pd.read_parquet(
            one_path
        ),
        symbol,
    )

    fifteen = (
        prepare_fifteen_minute_frame(
            pd.read_parquet(
                fifteen_path
            ),
            symbol,
        )
    )

    return (
        one_hour,
        fifteen,
        one_path,
        fifteen_path,
    )


def full_history_eligibility(
    one_hour: pd.DataFrame,
    fifteen: pd.DataFrame,
    *,
    maximum_start_lag_days: float = 7.0,
    maximum_end_lag_days: float = 2.0,
) -> dict:
    first_1h = utc_timestamp(
        one_hour["date"].min()
    )

    last_1h = utc_timestamp(
        one_hour["date"].max()
    )

    first_15m = utc_timestamp(
        fifteen["date"].min()
    )

    last_15m = utc_timestamp(
        fifteen["date"].max()
    )

    start_lag_days = (
        first_15m
        - first_1h
    ).total_seconds() / 86400.0

    end_lag_days = (
        last_1h
        - last_15m
    ).total_seconds() / 86400.0

    eligible = (
        start_lag_days
        <= maximum_start_lag_days
        and end_lag_days
        <= maximum_end_lag_days
    )

    return {
        "eligible": bool(
            eligible
        ),
        "first_1h": (
            first_1h.isoformat()
        ),
        "last_1h": (
            last_1h.isoformat()
        ),
        "first_15m": (
            first_15m.isoformat()
        ),
        "last_15m": (
            last_15m.isoformat()
        ),
        "start_lag_days": float(
            start_lag_days
        ),
        "end_lag_days": float(
            end_lag_days
        ),
    }


def session_bounds(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    calendar = mcal.get_calendar(
        "NYSE"
    )

    schedule = calendar.schedule(
        start_date=(
            utc_timestamp(start)
            .tz_convert(
                "America/New_York"
            )
            .date()
        ),
        end_date=(
            utc_timestamp(end)
            .tz_convert(
                "America/New_York"
            )
            .date()
        ),
    )

    output = {}

    for session, row in (
        schedule.iterrows()
    ):
        market_open = utc_timestamp(
            row["market_open"]
        )

        market_close = utc_timestamp(
            row["market_close"]
        )

        output[
            session.date()
        ] = (
            market_open,
            market_close,
        )

    return output


def expected_15m_times(
    hour_start: pd.Timestamp,
    bounds: Mapping,
) -> pd.DatetimeIndex:
    hour_start = utc_timestamp(
        hour_start
    )

    session_date = (
        hour_start
        .tz_convert(
            "America/New_York"
        )
        .date()
    )

    if session_date not in bounds:
        raise ValueError(
            "1h bar has no NYSE session"
        )

    market_open, market_close = (
        bounds[
            session_date
        ]
    )

    if (
        hour_start
        < market_open
        or hour_start
        >= market_close
    ):
        raise ValueError(
            "1h bar outside NYSE RTH"
        )

    hour_end = min(
        hour_start
        + ONE_HOUR,
        market_close,
    )

    return pd.date_range(
        start=hour_start,
        end=(
            hour_end
            - FIFTEEN_MINUTES
        ),
        freq="15min",
        tz="UTC",
    )


def complete_hour_bars(
    fifteen: pd.DataFrame,
    hour_start: pd.Timestamp,
    bounds: Mapping,
) -> tuple[
    pd.DataFrame,
    pd.DatetimeIndex,
]:
    expected = expected_15m_times(
        hour_start,
        bounds,
    )

    indexed = (
        fifteen
        .set_index(
            "date",
            drop=False,
        )
    )

    missing = expected.difference(
        indexed.index
    )

    if len(missing):
        return (
            indexed.iloc[
                0:0
            ].copy(),
            missing,
        )

    bars = (
        indexed.loc[
            expected
        ]
        .sort_index()
        .copy()
    )

    return (
        bars,
        missing,
    )


def first_limit_fill(
    bars: pd.DataFrame,
    *,
    level: float,
) -> dict | None:
    touched = bars.loc[
        pd.to_numeric(
            bars["low"],
            errors="coerce",
        )
        <= float(level)
    ]

    if touched.empty:
        return None

    row = touched.iloc[0]

    open_price = float(
        row["open"]
    )

    entry_price = min(
        open_price,
        float(level),
    )

    return {
        "time": utc_timestamp(
            row["date"]
        ),
        "price": float(
            entry_price
        ),
        "gap_fill": bool(
            open_price
            < float(level)
        ),
    }


def first_stop_fill(
    bars: pd.DataFrame,
    *,
    stop_price: float,
    not_before: pd.Timestamp,
) -> dict | None:
    not_before = utc_timestamp(
        not_before
    )

    eligible = bars.loc[
        pd.to_datetime(
            bars["date"],
            utc=True,
        )
        >= not_before
    ]

    hit = eligible.loc[
        pd.to_numeric(
            eligible["low"],
            errors="coerce",
        )
        <= float(
            stop_price
        )
    ]

    if hit.empty:
        return None

    row = hit.iloc[0]

    open_price = float(
        row["open"]
    )

    exit_price = (
        min(
            open_price,
            float(
                stop_price
            ),
        )
        if open_price
        < float(
            stop_price
        )
        else float(
            stop_price
        )
    )

    return {
        "time": utc_timestamp(
            row["date"]
        ),
        "price": float(
            exit_price
        ),
    }


def resolve_market_structure_symbol(
    one_hour: pd.DataFrame,
    fifteen: pd.DataFrame,
    *,
    symbol: str,
    hypothesis_id: str,
    params: Mapping,
) -> tuple[
    pd.DataFrame,
    dict,
]:
    symbol = symbol.upper()

    cache = FeatureCache(
        one_hour
    )

    breakout_lookback = int(
        params[
            "breakout_lookback"
        ]
    )

    atr_period = int(
        params[
            "atr_period"
        ]
    )

    pullback_atr = float(
        params[
            "pullback_atr"
        ]
    )

    valid_days = int(
        params[
            "valid_days"
        ]
    )

    stop_atr = float(
        params[
            "stop_atr"
        ]
    )

    exit_lookback = int(
        params[
            "exit_lookback"
        ]
    )

    dates = pd.DatetimeIndex(
        pd.to_datetime(
            one_hour[
                "date"
            ],
            utc=True,
        )
    )

    opens = cache.arr(
        "open"
    )

    lows = cache.arr(
        "low"
    )

    closes = cache.arr(
        "close"
    )

    atr = cache.atr(
        atr_period
    )

    prior_high = (
        cache.rolling_max(
            "high",
            breakout_lookback,
            shift=1,
        )
    )

    exit_high = (
        cache.rolling_max(
            "high",
            exit_lookback,
            shift=1,
        )
    )

    breakouts = np.flatnonzero(
        (
            closes
            > prior_high
        )
        & np.isfinite(
            atr
        )
        & np.isfinite(
            prior_high
        )
    )

    bounds = session_bounds(
        dates.min(),
        dates.max(),
    )

    rows = []

    last_exit = -1

    required_15m_hours = 0
    complete_15m_hours = 0
    path_complete = True
    path_failure = None
    path_failure_time = None

    for breakout_index in (
        breakouts
    ):
        if (
            breakout_index
            < last_exit
        ):
            continue

        level = (
            lows[
                breakout_index
            ]
            - (
                pullback_atr
                * atr[
                    breakout_index
                ]
            )
        )

        if (
            not math.isfinite(
                float(
                    level
                )
            )
        ):
            continue

        entry_exec = None
        entry_time = None
        entry_price = None
        entry_gap_fill = False

        entry_limit = min(
            len(
                one_hour
            ),
            (
                breakout_index
                + 1
                + valid_days
            ),
        )

        for hour_index in range(
            breakout_index + 1,
            entry_limit,
        ):
            if (
                lows[
                    hour_index
                ]
                > level
            ):
                continue

            required_15m_hours += 1

            bars, missing = (
                complete_hour_bars(
                    fifteen,
                    dates[
                        hour_index
                    ],
                    bounds,
                )
            )

            if len(missing):
                path_complete = False
                path_failure = (
                    "ENTRY_TOUCH_HOUR_"
                    "MISSING_15M"
                )
                path_failure_time = (
                    dates[
                        hour_index
                    ]
                )
                break

            complete_15m_hours += 1

            fill = first_limit_fill(
                bars,
                level=float(
                    level
                ),
            )

            if fill is None:
                path_complete = False
                path_failure = (
                    "ONE_HOUR_LOW_"
                    "NOT_REPRODUCED_15M"
                )
                path_failure_time = (
                    dates[
                        hour_index
                    ]
                )
                break

            entry_exec = hour_index
            entry_time = fill[
                "time"
            ]
            entry_price = float(
                fill[
                    "price"
                ]
            )
            entry_gap_fill = bool(
                fill[
                    "gap_fill"
                ]
            )

            break

        if not path_complete:
            break

        if (
            entry_exec is None
            or entry_time is None
            or entry_price is None
            or entry_price <= 0
        ):
            continue

        stop_price = (
            entry_price
            - (
                stop_atr
                * atr[
                    breakout_index
                ]
            )
        )

        exit_exec = (
            len(
                one_hour
            )
            - 1
        )

        exit_time = dates[
            -1
        ]

        exit_price = float(
            closes[
                -1
            ]
        )

        forced = True
        exit_reason = (
            "FORCED_END"
        )

        for hour_index in range(
            entry_exec,
            len(
                one_hour
            )
            - 1,
        ):
            if (
                lows[
                    hour_index
                ]
                <= stop_price
            ):
                required_15m_hours += 1

                bars, missing = (
                    complete_hour_bars(
                        fifteen,
                        dates[
                            hour_index
                        ],
                        bounds,
                    )
                )

                if len(missing):
                    path_complete = False
                    path_failure = (
                        "STOP_TOUCH_HOUR_"
                        "MISSING_15M"
                    )
                    path_failure_time = (
                        dates[
                            hour_index
                        ]
                    )
                    break

                complete_15m_hours += 1

                stop = first_stop_fill(
                    bars,
                    stop_price=float(
                        stop_price
                    ),
                    not_before=(
                        entry_time
                        if hour_index
                        == entry_exec
                        else dates[
                            hour_index
                        ]
                    ),
                )

                if stop is not None:
                    exit_exec = (
                        hour_index
                    )

                    exit_time = stop[
                        "time"
                    ]

                    exit_price = float(
                        stop[
                            "price"
                        ]
                    )

                    forced = False
                    exit_reason = (
                        "STOP_15M"
                    )

                    break

            if (
                closes[
                    hour_index
                ]
                > exit_high[
                    hour_index
                ]
            ):
                exit_exec = (
                    hour_index
                    + 1
                )

                exit_time = dates[
                    exit_exec
                ]

                exit_price = float(
                    opens[
                        exit_exec
                    ]
                )

                forced = False
                exit_reason = (
                    "STRUCTURAL_"
                    "1H_NEXT_OPEN"
                )

                break

        if not path_complete:
            break

        if (
            not math.isfinite(
                exit_price
            )
            or exit_price <= 0
        ):
            path_complete = False
            path_failure = (
                "INVALID_EXIT_PRICE"
            )
            path_failure_time = (
                exit_time
            )
            break

        gross_return = (
            exit_price
            / entry_price
            - 1.0
        )

        score = (
            closes[
                breakout_index
            ]
            / prior_high[
                breakout_index
            ]
            - 1.0
        )

        rows.append(
            {
                "hypothesis_id": (
                    hypothesis_id
                ),
                "strategy": (
                    "market_structure_"
                    "atr_pullback"
                ),
                "family": (
                    "breakout_pullback"
                ),
                "symbol": symbol,
                "breakout_time": (
                    dates[
                        breakout_index
                    ]
                ),
                "entry_time": (
                    entry_time
                ),
                "exit_time": (
                    exit_time
                ),
                "entry_level": float(
                    level
                ),
                "entry_price": float(
                    entry_price
                ),
                "stop_price": float(
                    stop_price
                ),
                "exit_price": float(
                    exit_price
                ),
                "gross_return": float(
                    gross_return
                ),
                "score": float(
                    score
                ),
                "duration_bars": int(
                    max(
                        exit_exec
                        - entry_exec,
                        0,
                    )
                ),
                "forced": bool(
                    forced
                ),
                "exit_reason": (
                    exit_reason
                ),
                "entry_gap_fill": bool(
                    entry_gap_fill
                ),
                "same_1h_entry_exit": bool(
                    exit_exec
                    == entry_exec
                ),
                "same_15m_entry_exit": bool(
                    utc_timestamp(
                        exit_time
                    )
                    == utc_timestamp(
                        entry_time
                    )
                ),
                "execution_resolution": (
                    "REAL_15M_CHRONOLOGY"
                ),
            }
        )

        last_exit = exit_exec

    frame = pd.DataFrame(
        rows
    )

    if not frame.empty:
        frame = (
            frame.sort_values(
                [
                    "entry_time",
                    "symbol",
                ]
            )
            .reset_index(
                drop=True
            )
        )

    audit = {
        "symbol": symbol,
        "hypothesis_id": (
            hypothesis_id
        ),
        "path_complete": bool(
            path_complete
        ),
        "path_failure": (
            path_failure
        ),
        "path_failure_time": (
            (
                utc_timestamp(
                    path_failure_time
                ).isoformat()
            )
            if path_failure_time
            is not None
            else None
        ),
        "resolved_trades": int(
            len(
                frame
            )
        ),
        "required_15m_hours": int(
            required_15m_hours
        ),
        "complete_15m_hours": int(
            complete_15m_hours
        ),
        "threshold_hour_coverage": (
            float(
                complete_15m_hours
                / required_15m_hours
            )
            if required_15m_hours
            else 1.0
        ),
        "same_1h_entry_exit": int(
            (
                frame[
                    "same_1h_entry_exit"
                ]
                .sum()
            )
            if not frame.empty
            else 0
        ),
        "same_15m_entry_exit": int(
            (
                frame[
                    "same_15m_entry_exit"
                ]
                .sum()
            )
            if not frame.empty
            else 0
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    return (
        frame,
        audit,
    )
