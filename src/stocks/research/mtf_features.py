from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.data.timeframe_integrity import (
    assert_no_future_availability,
    with_availability,
)
from stocks.data.timeframe_pipeline import (
    TIMEFRAME_ORDER,
    TimeframePipeline,
    build_timeframe_pipeline,
)


CONTEXT_TIMEFRAMES = (
    "15m",
    "2h",
    "4h",
    "1d",
    "1w",
)


@dataclass(frozen=True)
class MTFDataset:
    symbol: str
    frame: pd.DataFrame
    available_timeframes: tuple[str, ...]
    missing_timeframes: tuple[str, ...]


def _numeric(
    series: pd.Series,
) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    ).astype(float)


def timeframe_state_features(
    frame: pd.DataFrame,
    *,
    prefix: str,
) -> pd.DataFrame:
    work = frame.copy()

    open_ = _numeric(
        work["open"]
    )

    high = _numeric(
        work["high"]
    )

    low = _numeric(
        work["low"]
    )

    close = _numeric(
        work["close"]
    )

    volume = _numeric(
        work["volume"]
    )

    safe_close = close.replace(
        0.0,
        np.nan,
    )

    safe_open = open_.replace(
        0.0,
        np.nan,
    )

    returns = close.pct_change(
        fill_method=None
    )

    log_volume = np.log1p(
        volume.clip(
            lower=0.0
        )
    )

    volume_mean = (
        log_volume
        .rolling(
            20,
            min_periods=5,
        )
        .mean()
    )

    volume_std = (
        log_volume
        .rolling(
            20,
            min_periods=5,
        )
        .std()
        .replace(
            0.0,
            np.nan,
        )
    )

    ema5 = close.ewm(
        span=5,
        adjust=False,
        min_periods=3,
    ).mean()

    ema20 = close.ewm(
        span=20,
        adjust=False,
        min_periods=5,
    ).mean()

    result = pd.DataFrame(
        index=work.index
    )

    result[
        f"{prefix}_ret1"
    ] = returns

    result[
        f"{prefix}_ret3"
    ] = close.pct_change(
        periods=3,
        fill_method=None,
    )

    result[
        f"{prefix}_ret5"
    ] = close.pct_change(
        periods=5,
        fill_method=None,
    )

    result[
        f"{prefix}_range_pct"
    ] = (
        high - low
    ) / safe_close

    result[
        f"{prefix}_body_pct"
    ] = (
        close - open_
    ) / safe_open

    result[
        f"{prefix}_close_location"
    ] = (
        close - low
    ) / (
        high - low
    ).replace(
        0.0,
        np.nan,
    )

    result[
        f"{prefix}_ema5_rel"
    ] = (
        close / ema5 - 1.0
    )

    result[
        f"{prefix}_ema20_rel"
    ] = (
        close / ema20 - 1.0
    )

    result[
        f"{prefix}_realized_vol5"
    ] = returns.rolling(
        5,
        min_periods=3,
    ).std()

    result[
        f"{prefix}_realized_vol20"
    ] = returns.rolling(
        20,
        min_periods=5,
    ).std()

    result[
        f"{prefix}_volume_z20"
    ] = (
        log_volume
        - volume_mean
    ) / volume_std

    return (
        result
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )


def decision_surface(
    pipeline: TimeframePipeline,
) -> pd.DataFrame:
    one_hour = (
        pipeline.views.get(
            "1h"
        )
    )

    if one_hour is None:
        raise ValueError(
            f"{pipeline.symbol}: "
            "1h decision surface missing"
        )

    available = with_availability(
        one_hour.frame,
        timeframe="1h",
    )

    assert_no_future_availability(
        available
    )

    result = pd.DataFrame(
        {
            "decision_time": (
                available[
                    "availability_time"
                ]
            ),
            "decision_bar_time": (
                available[
                    "bar_time"
                ]
            ),
            "decision_close": (
                available[
                    "close"
                ].astype(float)
            ),
        }
    )

    result[
        "decision_time"
    ] = pd.to_datetime(
        result[
            "decision_time"
        ],
        utc=True,
    ).astype(
        "datetime64[ns, UTC]"
    )

    result[
        "decision_bar_time"
    ] = pd.to_datetime(
        result[
            "decision_bar_time"
        ],
        utc=True,
    ).astype(
        "datetime64[ns, UTC]"
    )

    result = (
        result.sort_values(
            [
                "decision_time",
                "decision_bar_time",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    duplicate_mask = (
        result[
            "decision_time"
        ].duplicated(
            keep=False
        )
    )

    if duplicate_mask.any():
        duplicates = result.loc[
            duplicate_mask
        ].copy()

        invalid = (
            duplicates[
                "decision_bar_time"
            ]
            >
            duplicates[
                "decision_time"
            ]
        )

        if invalid.any():
            raise ValueError(
                "duplicate decision times "
                "contain future 1h bars"
            )

        result = (
            result.groupby(
                "decision_time",
                sort=True,
                as_index=False,
            )
            .tail(1)
            .sort_values(
                "decision_time"
            )
            .reset_index(
                drop=True
            )
        )

    if (
        result[
            "decision_time"
        ].duplicated().any()
    ):
        raise ValueError(
            "duplicate 1h decision times "
            "remain after causal collapse"
        )

    if (
        result[
            "decision_bar_time"
        ]
        >
        result[
            "decision_time"
        ]
    ).any():
        raise ValueError(
            "1h decision surface "
            "contains future bar"
        )

    return result


def _context_for_join(
    pipeline: TimeframePipeline,
    timeframe: str,
) -> pd.DataFrame:
    view = pipeline.views.get(
        timeframe
    )

    if view is None:
        raise KeyError(
            timeframe
        )

    available = with_availability(
        view.frame,
        timeframe=timeframe,
    )

    assert_no_future_availability(
        available
    )

    if available.empty:
        return pd.DataFrame()

    feature_source = available[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].copy()

    features = (
        timeframe_state_features(
            feature_source,
            prefix=timeframe,
        )
    )

    result = features.copy()

    source_column = (
        f"{timeframe}_"
        "source_bar_time"
    )

    availability_column = (
        f"{timeframe}_"
        "availability_time"
    )

    result[
        source_column
    ] = pd.to_datetime(
        available[
            "bar_time"
        ],
        utc=True,
    )

    result[
        availability_column
    ] = pd.to_datetime(
        available[
            "availability_time"
        ],
        utc=True,
    )

    result[
        source_column
    ] = result[
        source_column
    ].astype(
        "datetime64[ns, UTC]"
    )

    result[
        availability_column
    ] = result[
        availability_column
    ].astype(
        "datetime64[ns, UTC]"
    )

    result = (
        result.dropna(
            subset=[
                availability_column
            ]
        )
        .reset_index(
            drop=True
        )
        .sort_values(
            availability_column
        )
        .reset_index(
            drop=True
        )
    )

    return result



INTRADAY_SAME_SESSION_TIMEFRAMES = frozenset(
    {
        "15m",
        "2h",
        "4h",
    }
)


def _nyse_session_key(
    series: pd.Series,
) -> pd.Series:
    values = pd.to_datetime(
        series,
        utc=True,
        errors="coerce",
    )

    return (
        values
        .dt.tz_convert(
            "America/New_York"
        )
        .dt.strftime(
            "%Y-%m-%d"
        )
    )


def apply_context_freshness(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    result = frame.copy()

    source_column = (
        f"{timeframe}_source_bar_time"
    )

    availability_column = (
        f"{timeframe}_availability_time"
    )

    age_column = (
        f"{timeframe}_age_minutes"
    )

    available = (
        result[
            source_column
        ].notna()
        &
        result[
            availability_column
        ].notna()
    )

    if timeframe in (
        INTRADAY_SAME_SESSION_TIMEFRAMES
    ):
        decision_session = (
            _nyse_session_key(
                result[
                    "decision_time"
                ]
            )
        )

        source_session = (
            _nyse_session_key(
                result[
                    source_column
                ]
            )
        )

        available = (
            available
            &
            decision_session.eq(
                source_session
            )
        )

    stale = ~available

    if feature_columns:
        result.loc[
            stale,
            feature_columns,
        ] = np.nan

    result.loc[
        stale,
        source_column,
    ] = pd.NaT

    result.loc[
        stale,
        availability_column,
    ] = pd.NaT

    if age_column in result:
        result.loc[
            stale,
            age_column,
        ] = np.nan

    result[
        f"{timeframe}_available"
    ] = available.astype(
        "int8"
    )

    return result


def build_causal_mtf_dataset(
    project_root: str | Path,
    symbol: str,
) -> MTFDataset:
    pipeline = (
        build_timeframe_pipeline(
            project_root,
            symbol,
        )
    )

    decision = decision_surface(
        pipeline
    )

    available_context = []
    missing_context = []

    result = decision.copy()

    for timeframe in (
        CONTEXT_TIMEFRAMES
    ):
        if timeframe not in (
            pipeline.views
        ):
            missing_context.append(
                timeframe
            )
            continue

        context = _context_for_join(
            pipeline,
            timeframe,
        )

        source_column = (
            f"{timeframe}_"
            "source_bar_time"
        )

        availability_column = (
            f"{timeframe}_"
            "availability_time"
        )

        context_feature_columns = [
            column
            for column
            in context.columns
            if (
                column.startswith(
                    f"{timeframe}_"
                )
                and column
                not in {
                    source_column,
                    availability_column,
                }
            )
        ]

        result[
            "decision_time"
        ] = pd.to_datetime(
            result[
                "decision_time"
            ],
            utc=True,
        ).astype(
            "datetime64[ns, UTC]"
        )

        context[
            availability_column
        ] = pd.to_datetime(
            context[
                availability_column
            ],
            utc=True,
        ).astype(
            "datetime64[ns, UTC]"
        )

        result = pd.merge_asof(
            result.sort_values(
                "decision_time"
            ),
            context.sort_values(
                availability_column
            ),
            left_on=(
                "decision_time"
            ),
            right_on=(
                availability_column
            ),
            direction="backward",
            allow_exact_matches=True,
        )

        matched = result[
            availability_column
        ].notna()

        invalid = (
            matched
            &
            (
                result[
                    availability_column
                ]
                >
                result[
                    "decision_time"
                ]
            )
        )

        if invalid.any():
            raise ValueError(
                f"{symbol} {timeframe}: "
                "future context leaked into "
                "decision surface"
            )

        age_seconds = (
            result[
                "decision_time"
            ]
            -
            result[
                availability_column
            ]
        ).dt.total_seconds()

        result[
            f"{timeframe}_age_minutes"
        ] = (
            age_seconds
            / 60.0
        )

        result = apply_context_freshness(
            result,
            timeframe=timeframe,
            feature_columns=(
                context_feature_columns
            ),
        )

        available_context.append(
            timeframe
        )

    result[
        "symbol"
    ] = symbol.upper()

    return MTFDataset(
        symbol=symbol.upper(),
        frame=result,
        available_timeframes=tuple(
            available_context
        ),
        missing_timeframes=tuple(
            missing_context
        ),
    )
