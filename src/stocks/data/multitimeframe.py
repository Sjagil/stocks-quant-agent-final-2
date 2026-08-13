from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    validate_canonical,
    write_canonical_parquet,
)


ACTIVE_SWING_TIMEFRAMES = ("15m", "1h", "2h", "4h", "1d", "1w")


@dataclass(frozen=True)
class ActiveSwingBundle:
    symbol: str
    frames: dict[str, pd.DataFrame]
    source_paths: dict[str, Path]

    @property
    def available_timeframes(self) -> tuple[str, ...]:
        return tuple(
            tf for tf in ACTIVE_SWING_TIMEFRAMES
            if tf in self.frames
        )


def _aggregate_intraday(
    frame: pd.DataFrame,
    *,
    ratio: int,
    exchange_timezone: str,
    drop_partial: bool = True,
) -> pd.DataFrame:
    work = canonicalize_ohlcv(frame).copy()

    local_index = work.index.tz_convert(exchange_timezone)
    work["_session"] = [str(value.date()) for value in local_index]
    work["_ordinal"] = work.groupby("_session").cumcount()
    work["_bucket"] = (
        work["_session"]
        + ":"
        + (work["_ordinal"] // ratio).astype(str)
    )

    grouped = work.groupby("_bucket", sort=True)

    result = grouped.agg(
        timestamp=("open", lambda x: x.index[0]),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        source_bar_count=("open", "size"),
    )

    result = result.set_index("timestamp")

    if drop_partial:
        result = result.loc[result["source_bar_count"] >= ratio]

    result = result.drop(columns=["source_bar_count"])
    result = canonicalize_ohlcv(result)
    validate_canonical(result)
    return result


def _aggregate_weekly(
    frame: pd.DataFrame,
    *,
    exchange_timezone: str,
    drop_partial: bool = True,
) -> pd.DataFrame:
    work = canonicalize_ohlcv(frame).copy()

    local = work.index.tz_convert(exchange_timezone).tz_localize(None)
    periods = local.to_period("W-FRI")

    work["_period"] = periods.astype(str)

    grouped = work.groupby("_period", sort=True)

    result = grouped.agg(
        timestamp=("open", lambda x: x.index[0]),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).set_index("timestamp")

    if drop_partial and len(result):
        final_period = periods[-1]
        final_source_date = local[-1].date()
        if final_source_date < final_period.end_time.date():
            result = result.iloc[:-1]

    result = canonicalize_ohlcv(result)
    validate_canonical(result)
    return result


def aggregate_bars(
    frame: pd.DataFrame,
    *,
    source_timeframe: str,
    target_timeframe: str,
    exchange_timezone: str = "America/New_York",
) -> pd.DataFrame:
    allowed = {
        ("5m", "15m"): 3,
        ("15m", "1h"): 4,
        ("1h", "2h"): 2,
        ("1h", "4h"): 4,
    }

    pair = (source_timeframe, target_timeframe)

    if pair in allowed:
        return _aggregate_intraday(
            frame,
            ratio=allowed[pair],
            exchange_timezone=exchange_timezone,
        )

    if pair == ("1d", "1w"):
        return _aggregate_weekly(
            frame,
            exchange_timezone=exchange_timezone,
        )

    raise ValueError(
        f"unsupported causal aggregation: "
        f"{source_timeframe}->{target_timeframe}"
    )


def _candidate_paths(
    root: Path,
    symbol: str,
    timeframe: str,
) -> tuple[Path, ...]:
    symbol = symbol.upper()

    if timeframe == "1h":
        return (
            root
            / "data"
            / "canonical"
            / "provider_fabric"
            / f"{symbol}_1h.parquet",
            root / "data" / "adjusted" / f"{symbol}_1h.parquet",
            root / "data" / "derived" / f"{symbol}_1h.parquet",
            root / "data" / "processed" / f"{symbol}_1h.parquet",
        )

    if timeframe == "15m":
        return (
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
            root / "data" / "derived" / f"{symbol}_15m.parquet",
            root / "data" / "processed" / f"{symbol}_15m.parquet",
            root / "data" / "adjusted" / f"{symbol}_15m.parquet",
        )

    return (
        root / "data" / "processed" / f"{symbol}_{timeframe}.parquet",
        root / "data" / "adjusted" / f"{symbol}_{timeframe}.parquet",
        root / "data" / "derived" / f"{symbol}_{timeframe}.parquet",
    )


def discover_local_frames(
    project_root: str | Path,
    symbol: str,
) -> tuple[dict[str, pd.DataFrame], dict[str, Path]]:
    root = Path(project_root).resolve()

    frames: dict[str, pd.DataFrame] = {}
    paths: dict[str, Path] = {}

    for timeframe in ("5m", "15m", "1h", "1d"):
        for candidate in _candidate_paths(root, symbol, timeframe):
            if candidate.is_file():
                frame = canonicalize_ohlcv(pd.read_parquet(candidate))
                validate_canonical(frame)
                frames[timeframe] = frame
                paths[timeframe] = candidate
                break

    return frames, paths


def build_active_swing_bundle(
    symbol: str,
    source_frames: Mapping[str, pd.DataFrame],
    *,
    exchange_timezone: str = "America/New_York",
) -> ActiveSwingBundle:
    frames = {
        tf: canonicalize_ohlcv(frame)
        for tf, frame in source_frames.items()
        if frame is not None and not frame.empty
    }

    for frame in frames.values():
        validate_canonical(frame)

    if "15m" not in frames and "5m" in frames:
        frames["15m"] = aggregate_bars(
            frames["5m"],
            source_timeframe="5m",
            target_timeframe="15m",
            exchange_timezone=exchange_timezone,
        )

    if "1h" not in frames and "15m" in frames:
        frames["1h"] = aggregate_bars(
            frames["15m"],
            source_timeframe="15m",
            target_timeframe="1h",
            exchange_timezone=exchange_timezone,
        )

    if "1h" in frames:
        frames["2h"] = aggregate_bars(
            frames["1h"],
            source_timeframe="1h",
            target_timeframe="2h",
            exchange_timezone=exchange_timezone,
        )
        frames["4h"] = aggregate_bars(
            frames["1h"],
            source_timeframe="1h",
            target_timeframe="4h",
            exchange_timezone=exchange_timezone,
        )

    if "1d" in frames:
        frames["1w"] = aggregate_bars(
            frames["1d"],
            source_timeframe="1d",
            target_timeframe="1w",
            exchange_timezone=exchange_timezone,
        )

    return ActiveSwingBundle(
        symbol=symbol.upper(),
        frames=frames,
        source_paths={},
    )


def load_active_swing_bundle(
    project_root: str | Path,
    symbol: str,
    *,
    exchange_timezone: str = "America/New_York",
) -> ActiveSwingBundle:
    frames, paths = discover_local_frames(project_root, symbol)

    bundle = build_active_swing_bundle(
        symbol,
        frames,
        exchange_timezone=exchange_timezone,
    )

    return ActiveSwingBundle(
        symbol=bundle.symbol,
        frames=bundle.frames,
        source_paths=paths,
    )


def materialize_bundle(
    project_root: str | Path,
    bundle: ActiveSwingBundle,
) -> dict[str, str]:
    root = Path(project_root).resolve()
    output: dict[str, str] = {}

    for timeframe, frame in bundle.frames.items():
        target = (
            root
            / "data"
            / "derived"
            / f"{bundle.symbol}_{timeframe}.parquet"
        )

        write_canonical_parquet(
            frame,
            target,
            CanonicalMetadata(
                symbol=bundle.symbol,
                timeframe=timeframe,
                source="LOCAL_ACTIVE_SWING_DATA_PLANE",
                adjustment="provider_or_source_preserved",
                provenance={
                    "derived": timeframe not in bundle.source_paths,
                    "source_paths": {
                        key: str(value)
                        for key, value in bundle.source_paths.items()
                    },
                },
            ),
        )

        output[timeframe] = str(target)

    return output
