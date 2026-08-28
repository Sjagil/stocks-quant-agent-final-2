from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

REQUIRED = ("open", "high", "low", "close", "volume")


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _canonical_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=list(REQUIRED),
            index=pd.DatetimeIndex([], tz="UTC", name="timestamp"),
        )
    work = frame.copy()
    if "timestamp" in work.columns:
        work = work.set_index("timestamp")
    elif "date" in work.columns:
        work = work.set_index("date")
    work.index = pd.DatetimeIndex(pd.to_datetime(work.index, utc=True), name="timestamp")
    work.columns = [str(c).strip().lower() for c in work.columns]
    missing = [c for c in REQUIRED if c not in work.columns]
    if missing:
        raise ValueError(f"IBKR historical bars missing columns: {missing}")
    work = work[list(REQUIRED)]
    for c in REQUIRED:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    if work[list(REQUIRED)].isna().any().any():
        raise ValueError("IBKR historical bars contain missing OHLCV values")
    if not np.isfinite(work[list(REQUIRED)].to_numpy(dtype=float)).all():
        raise ValueError("IBKR historical bars contain non-finite OHLCV values")
    if (work[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("IBKR historical bars contain non-positive prices")
    if (work["volume"] < 0).any():
        raise ValueError("IBKR historical bars contain negative volume")
    if work.index.duplicated().any():
        raise ValueError("IBKR historical bars contain duplicate timestamps")
    if (work["high"] < work[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("IBKR historical bars contain invalid highs")
    if (work["low"] > work[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("IBKR historical bars contain invalid lows")
    return work.sort_index(kind="stable")


@dataclass(frozen=True)
class SessionWindowV2412:
    market_open: str
    market_close: str
    market_open_now: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrossProviderCheckV2412:
    passed: bool
    overlap_bars: int
    required_overlap_bars: int
    max_close_disagreement_bps: float | None
    allowed_close_disagreement_bps: float
    median_close_disagreement_bps: float | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def latest_opened_session(
    now: pd.Timestamp,
    calendar_name: str = "NYSE",
) -> tuple[pd.Timestamp, pd.Timestamp, bool]:
    now = _utc(now)
    cal = mcal.get_calendar(calendar_name)
    schedule = cal.schedule(
        start_date=(now - pd.Timedelta(days=10)).date().isoformat(),
        end_date=(now + pd.Timedelta(days=1)).date().isoformat(),
    )
    if schedule.empty:
        raise ValueError("market calendar returned no sessions")
    opens = pd.to_datetime(schedule["market_open"], utc=True)
    closes = pd.to_datetime(schedule["market_close"], utc=True)
    eligible = schedule.loc[opens <= now]
    if eligible.empty:
        raise ValueError("no market session has opened before current time")
    row = eligible.iloc[-1]
    market_open = _utc(row["market_open"])
    market_close = _utc(row["market_close"])
    return market_open, market_close, bool(market_open <= now <= market_close)


def closed_latest_session_bars(
    frame: pd.DataFrame,
    *,
    now: pd.Timestamp,
    calendar_name: str,
    bar_period: pd.Timedelta,
    close_lag: pd.Timedelta,
) -> tuple[pd.DataFrame, SessionWindowV2412]:
    work = _canonical_frame(frame)
    market_open, market_close, market_open_now = latest_opened_session(now, calendar_name)
    cutoff = _utc(now) - close_lag
    in_session = work.loc[(work.index >= market_open) & (work.index < market_close)].copy()
    if in_session.empty:
        return in_session, SessionWindowV2412(
            market_open.isoformat(), market_close.isoformat(), market_open_now
        )

    ends = pd.DatetimeIndex(
        [min(ts + bar_period, market_close) for ts in in_session.index],
        tz="UTC",
    )
    closed = in_session.loc[ends <= cutoff].copy()
    return closed, SessionWindowV2412(
        market_open.isoformat(), market_close.isoformat(), market_open_now
    )


def cross_provider_close_check(
    historical: pd.DataFrame,
    ibkr_recent: pd.DataFrame,
    *,
    minimum_overlap_bars: int,
    maximum_close_disagreement_bps: float,
) -> CrossProviderCheckV2412:
    hist = _canonical_frame(historical)
    ibkr = _canonical_frame(ibkr_recent)
    common = hist.index.intersection(ibkr.index)
    required = int(minimum_overlap_bars)
    allowed = float(maximum_close_disagreement_bps)
    if len(common) < required:
        return CrossProviderCheckV2412(
            False, len(common), required, None, allowed, None,
            "CROSS_PROVIDER_OVERLAP_INSUFFICIENT",
        )
    h = hist.loc[common, "close"].astype(float)
    i = ibkr.loc[common, "close"].astype(float)
    denominator = ((h.abs() + i.abs()) / 2.0).replace(0, np.nan)
    disagreement = ((h - i).abs() / denominator * 10000.0).replace([np.inf, -np.inf], np.nan)
    if disagreement.isna().any():
        return CrossProviderCheckV2412(
            False, len(common), required, None, allowed, None,
            "CROSS_PROVIDER_DISAGREEMENT_UNCOMPUTABLE",
        )
    max_bps = float(disagreement.max())
    median_bps = float(disagreement.median())
    return CrossProviderCheckV2412(
        max_bps <= allowed,
        len(common), required, max_bps, allowed, median_bps,
        "CROSS_PROVIDER_MATCH" if max_bps <= allowed else "CROSS_PROVIDER_CLOSE_DISAGREEMENT",
    )


def merge_overlay(
    historical: pd.DataFrame,
    overlay: pd.DataFrame,
) -> pd.DataFrame:
    hist = _canonical_frame(historical)
    over = _canonical_frame(overlay)
    if over.empty:
        raise ValueError("current-session overlay contains no closed bars")
    merged = pd.concat([hist, over], axis=0)
    merged = merged.loc[~merged.index.duplicated(keep="last")].sort_index(kind="stable")
    return _canonical_frame(merged)
