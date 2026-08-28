from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv, validate_canonical
from stocks.data.multitimeframe import (
    ACTIVE_SWING_TIMEFRAMES,
    build_active_swing_bundle,
    discover_local_frames,
)


@dataclass(frozen=True)
class CandleBundle:
    symbol: str
    frames: dict[str, pd.DataFrame]
    source_paths: dict[str, Path]
    close_only: bool = True
    execution_authority: str = "NONE"


def _closed_only(frame: pd.DataFrame) -> pd.DataFrame:
    work = canonicalize_ohlcv(frame)
    validate_canonical(work)

    if not work.index.is_monotonic_increasing:
        raise ValueError("candle timestamps must be monotonic")
    if work.index.has_duplicates:
        raise ValueError("duplicate candle timestamps are forbidden")
    if (work["high"] < work["low"]).any():
        raise ValueError("invalid OHLC: high < low")
    if (
        (work["high"] < work[["open", "close"]].max(axis=1))
        | (work["low"] > work[["open", "close"]].min(axis=1))
    ).any():
        raise ValueError("invalid OHLC envelope")

    # Canonical persisted bars are treated as closed observations.
    # The live data collector is responsible for never persisting an in-progress bar.
    return work


def load_candle_bundle(
    project_root: str | Path,
    symbol: str,
) -> CandleBundle:
    root = Path(project_root).resolve()
    local_frames, local_paths = discover_local_frames(root, symbol)
    if not local_frames:
        raise FileNotFoundError(f"{symbol}: no canonical candle sources")

    clean = {
        timeframe: _closed_only(frame)
        for timeframe, frame in local_frames.items()
    }
    bundle = build_active_swing_bundle(
        symbol.upper(),
        clean,
    )

    frames = {
        timeframe: _closed_only(frame)
        for timeframe, frame in bundle.frames.items()
        if timeframe in ACTIVE_SWING_TIMEFRAMES
    }

    return CandleBundle(
        symbol=symbol.upper(),
        frames=frames,
        source_paths=local_paths,
    )


def frame_for_timeframe(
    project_root: str | Path,
    symbol: str,
    timeframe: str,
) -> pd.DataFrame:
    bundle = load_candle_bundle(project_root, symbol)
    if timeframe not in bundle.frames:
        raise FileNotFoundError(
            f"{symbol}: timeframe {timeframe!r} unavailable; "
            f"available={sorted(bundle.frames)}"
        )
    return bundle.frames[timeframe].copy()


def candle_summary(
    frame: pd.DataFrame,
) -> dict[str, Any]:
    work = _closed_only(frame)
    return {
        "rows": int(len(work)),
        "start": work.index[0].isoformat() if len(work) else None,
        "end": work.index[-1].isoformat() if len(work) else None,
        "last_close": float(work["close"].iloc[-1]) if len(work) else None,
        "duplicates": int(work.index.duplicated().sum()),
        "execution_authority": "NONE",
    }
