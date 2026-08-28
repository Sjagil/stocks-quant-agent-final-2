from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

REQUIRED = ("open", "high", "low", "close", "volume")


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _canon(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=list(REQUIRED), index=pd.DatetimeIndex([], tz="UTC", name="timestamp"))
    work = frame.copy()
    if "timestamp" in work.columns:
        work = work.set_index("timestamp")
    elif "date" in work.columns:
        work = work.set_index("date")
    work.index = pd.DatetimeIndex(pd.to_datetime(work.index, utc=True), name="timestamp")
    work.columns = [str(c).strip().lower() for c in work.columns]
    missing = [c for c in REQUIRED if c not in work.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")
    work = work[list(REQUIRED)].apply(pd.to_numeric, errors="coerce")
    if work.isna().any().any():
        raise ValueError("missing OHLCV values")
    if not np.isfinite(work.to_numpy(dtype=float)).all():
        raise ValueError("non-finite OHLCV values")
    if work.index.duplicated().any():
        raise ValueError("duplicate timestamps")
    return work.sort_index(kind="stable")


@dataclass(frozen=True)
class AlignmentAuditV242:
    source_rows: int
    aligned_rows: int
    sessions: int
    source_bar_minutes: int
    target_bar_minutes: int
    incomplete_buckets_dropped: int
    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def align_ibkr_rth_to_eodhd_grid_v242(
    frame: pd.DataFrame,
    *,
    now: pd.Timestamp | None = None,
    calendar_name: str = "NYSE",
    source_bar_minutes: int = 30,
    target_bar_minutes: int = 60,
    close_lag_seconds: int = 120,
) -> tuple[pd.DataFrame, AlignmentAuditV242]:
    """Aggregate IBKR 30m RTH bars onto EODHD's session-anchored 1h grid.

    US EODHD hourly bars start at 09:30 ET and then 10:30, 11:30, ... .
    IBKR native 1-hour RTH bars use a 09:30 opening half-hour followed by
    clock-hour bars. Requesting 30m bars and aggregating from the session open
    yields equivalent windows without timestamp shifting or price fabrication.
    The final 15:30-16:00 ET bucket is a legitimate half-hour session tail.
    """
    work = _canon(frame)
    if work.empty:
        return work, AlignmentAuditV242(0, 0, 0, source_bar_minutes, target_bar_minutes, 0)
    if target_bar_minutes % source_bar_minutes != 0:
        raise ValueError("target bar size must be a multiple of source bar size")

    now_ts = _utc(now if now is not None else pd.Timestamp.now(tz="UTC"))
    cal = mcal.get_calendar(calendar_name)
    start = (work.index.min() - pd.Timedelta(days=2)).date().isoformat()
    end = (work.index.max() + pd.Timedelta(days=2)).date().isoformat()
    schedule = cal.schedule(start_date=start, end_date=end)
    schedule = schedule.copy()
    schedule["market_open"] = pd.to_datetime(schedule["market_open"], utc=True)
    schedule["market_close"] = pd.to_datetime(schedule["market_close"], utc=True)

    pieces: list[pd.DataFrame] = []
    dropped = 0
    used_sessions = 0
    ratio = target_bar_minutes // source_bar_minutes
    close_lag = pd.Timedelta(seconds=int(close_lag_seconds))

    for _, row in schedule.iterrows():
        market_open = _utc(row["market_open"])
        market_close = _utc(row["market_close"])
        session = work.loc[(work.index >= market_open) & (work.index < market_close)].copy()
        if session.empty:
            continue
        used_sessions += 1
        elapsed = ((session.index - market_open).total_seconds() // 60).astype(int)
        bucket_no = elapsed // int(target_bar_minutes)
        session["__bucket__"] = bucket_no
        rows: list[dict[str, Any]] = []
        stamps: list[pd.Timestamp] = []
        for bucket, group in session.groupby("__bucket__", sort=True):
            bucket_start = market_open + pd.Timedelta(minutes=int(bucket) * target_bar_minutes)
            bucket_end = min(bucket_start + pd.Timedelta(minutes=target_bar_minutes), market_close)
            expected_minutes = int((bucket_end - bucket_start).total_seconds() // 60)
            expected_source_rows = max(1, int(np.ceil(expected_minutes / source_bar_minutes)))
            if len(group) < expected_source_rows:
                dropped += 1
                continue
            # Never admit a still-forming target bucket.
            if bucket_end > now_ts - close_lag:
                dropped += 1
                continue
            group = group.sort_index()
            rows.append({
                "open": float(group["open"].iloc[0]),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
                "close": float(group["close"].iloc[-1]),
                "volume": float(group["volume"].sum()),
            })
            stamps.append(bucket_start)
        if rows:
            part = pd.DataFrame(rows, index=pd.DatetimeIndex(stamps, name="timestamp", tz="UTC"))
            pieces.append(part)

    aligned = pd.concat(pieces).sort_index(kind="stable") if pieces else work.iloc[0:0].copy()
    aligned = _canon(aligned)
    return aligned, AlignmentAuditV242(
        source_rows=len(work),
        aligned_rows=len(aligned),
        sessions=used_sessions,
        source_bar_minutes=int(source_bar_minutes),
        target_bar_minutes=int(target_bar_minutes),
        incomplete_buckets_dropped=int(dropped),
    )
