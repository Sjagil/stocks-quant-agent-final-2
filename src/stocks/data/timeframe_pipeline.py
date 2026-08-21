from __future__ import annotations

from datetime import timedelta

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from stocks.data.canonical import (
    canonicalize_ohlcv,
    validate_canonical,
)
from stocks.data.multitimeframe import (
    load_active_swing_bundle,
)


TIMEFRAME_ORDER = (
    "15m",
    "1h",
    "2h",
    "4h",
    "1d",
    "1w",
)


@dataclass(frozen=True)
class TimeframeSpec:
    timeframe: str
    role: str
    mode: str
    source_timeframe: str
    window_bars: int | None = None


TIMEFRAME_SPECS = {
    "15m": TimeframeSpec(
        timeframe="15m",
        role="TACTICAL",
        mode="BAR",
        source_timeframe="15m",
    ),
    "1h": TimeframeSpec(
        timeframe="1h",
        role="CONFIRMATION",
        mode="BAR",
        source_timeframe="1h",
    ),
    "2h": TimeframeSpec(
        timeframe="2h",
        role="SETUP",
        mode="ROLLING_CONTEXT",
        source_timeframe="15m",
        window_bars=8,
    ),
    "4h": TimeframeSpec(
        timeframe="4h",
        role="SWING_DIRECTION",
        mode="ROLLING_CONTEXT",
        source_timeframe="15m",
        window_bars=16,
    ),
    "1d": TimeframeSpec(
        timeframe="1d",
        role="REGIME",
        mode="BAR",
        source_timeframe="1d",
    ),
    "1w": TimeframeSpec(
        timeframe="1w",
        role="STRUCTURE",
        mode="BAR",
        source_timeframe="1w",
    ),
}


@dataclass(frozen=True)
class TimeframeView:
    spec: TimeframeSpec
    frame: pd.DataFrame


@dataclass(frozen=True)
class TimeframePipeline:
    symbol: str
    views: dict[str, TimeframeView]

    @property
    def available_timeframes(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            timeframe
            for timeframe
            in TIMEFRAME_ORDER
            if timeframe in self.views
        )


def rolling_intraday_context(
    frame: pd.DataFrame,
    *,
    window_bars: int,
    exchange_timezone: str = (
        "America/New_York"
    ),
) -> pd.DataFrame:
    if window_bars < 1:
        raise ValueError(
            "window_bars must be >= 1"
        )

    work = canonicalize_ohlcv(
        frame
    ).copy()

    validate_canonical(
        work
    )

    local_index = (
        work.index
        .tz_convert(
            exchange_timezone
        )
    )

    work["_session"] = [
        value.date().isoformat()
        for value
        in local_index
    ]

    pieces = []

    expected_spacing = (
        timedelta(minutes=15)
    )

    for _, session in work.groupby(
        "_session",
        sort=True,
    ):
        session = session.drop(
            columns=[
                "_session",
            ]
        )

        if len(session) < window_bars:
            continue

        spacing = (
            session.index
            .to_series()
            .diff()
        )

        contiguous = spacing.eq(
            expected_spacing
        )

        run_id = (
            (~contiguous)
            .cumsum()
        )

        session[
            "_contiguous_run"
        ] = run_id.values

        for _, run in session.groupby(
            "_contiguous_run",
            sort=True,
        ):
            run = run.drop(
                columns=[
                    "_contiguous_run",
                ]
            )

            if len(run) < window_bars:
                continue

            result = pd.DataFrame(
                index=run.index
            )

            result["open"] = (
                run["open"]
                .shift(
                    window_bars - 1
                )
            )

            result["high"] = (
                run["high"]
                .rolling(
                    window=window_bars,
                    min_periods=window_bars,
                )
                .max()
            )

            result["low"] = (
                run["low"]
                .rolling(
                    window=window_bars,
                    min_periods=window_bars,
                )
                .min()
            )

            result["close"] = (
                run["close"]
            )

            result["volume"] = (
                run["volume"]
                .rolling(
                    window=window_bars,
                    min_periods=window_bars,
                )
                .sum()
            )

            result = result.dropna(
                subset=[
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            )

            if not result.empty:
                pieces.append(
                    result
                )

    if not pieces:
        return canonicalize_ohlcv(
            work.iloc[
                0:0
            ][
                [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ]
            ]
        )

    combined = pd.concat(
        pieces
    ).sort_index()

    combined = canonicalize_ohlcv(
        combined
    )

    validate_canonical(
        combined
    )

    return combined


def build_timeframe_pipeline(
    project_root: str | Path,
    symbol: str,
    *,
    exchange_timezone: str = (
        "America/New_York"
    ),
) -> TimeframePipeline:
    bundle = (
        load_active_swing_bundle(
            project_root,
            symbol,
            exchange_timezone=(
                exchange_timezone
            ),
        )
    )

    views: dict[
        str,
        TimeframeView,
    ] = {}

    for timeframe in (
        "15m",
        "1h",
        "1d",
        "1w",
    ):
        frame = bundle.frames.get(
            timeframe
        )

        if (
            frame is None
            or frame.empty
        ):
            continue

        views[
            timeframe
        ] = TimeframeView(
            spec=TIMEFRAME_SPECS[
                timeframe
            ],
            frame=frame,
        )

    fifteen = bundle.frames.get(
        "15m"
    )

    if (
        fifteen is not None
        and not fifteen.empty
    ):
        for timeframe in (
            "2h",
            "4h",
        ):
            spec = TIMEFRAME_SPECS[
                timeframe
            ]

            context = (
                rolling_intraday_context(
                    fifteen,
                    window_bars=int(
                        spec.window_bars
                    ),
                    exchange_timezone=(
                        exchange_timezone
                    ),
                )
            )

            if not context.empty:
                views[
                    timeframe
                ] = TimeframeView(
                    spec=spec,
                    frame=context,
                )

    return TimeframePipeline(
        symbol=symbol.upper(),
        views=views,
    )


def materialize_context_views(
    project_root: str | Path,
    pipeline: TimeframePipeline,
) -> dict[str, str]:
    root = Path(
        project_root
    ).resolve()

    output = {}

    target_root = (
        root
        / "data"
        / "derived"
    )

    target_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for timeframe in (
        "2h",
        "4h",
    ):
        view = pipeline.views.get(
            timeframe
        )

        if view is None:
            continue

        target = (
            target_root
            / (
                f"{pipeline.symbol}_"
                f"{timeframe}_context.parquet"
            )
        )

        view.frame.to_parquet(
            target
        )

        output[
            timeframe
        ] = str(
            target
        )

    return output
