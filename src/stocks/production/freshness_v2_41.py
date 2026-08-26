from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import timezone
from pathlib import Path

import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import read_canonical_parquet


@dataclass(frozen=True)
class FreshnessResult:
    symbol: str
    path: str
    rows: int
    latest: str | None
    expected_session_close: str | None
    age_from_expected_minutes: float | None
    passed: bool
    reason: str

    def to_dict(self):
        return asdict(self)


def _utc(ts) -> pd.Timestamp:
    x = pd.Timestamp(ts)
    return x.tz_localize("UTC") if x.tzinfo is None else x.tz_convert("UTC")


def expected_reference(now: pd.Timestamp, calendar_name: str = "NYSE") -> tuple[pd.Timestamp | None, bool]:
    now = _utc(now)
    cal = mcal.get_calendar(calendar_name)
    start = (now - pd.Timedelta(days=10)).date().isoformat()
    end = (now + pd.Timedelta(days=1)).date().isoformat()
    schedule = cal.schedule(start_date=start, end_date=end)
    if schedule.empty:
        return None, False

    schedule = schedule.copy()
    schedule["market_open"] = pd.to_datetime(schedule["market_open"], utc=True)
    schedule["market_close"] = pd.to_datetime(schedule["market_close"], utc=True)
    eligible = schedule.loc[schedule["market_open"] <= now]
    if eligible.empty:
        return None, False

    row = eligible.iloc[-1]
    market_open = _utc(row["market_open"])
    market_close = _utc(row["market_close"])
    market_open_now = market_open <= now <= market_close
    reference = now if market_open_now else market_close
    return reference, market_open_now


def check_file_freshness(
    symbol: str,
    path: str | Path,
    *,
    now: pd.Timestamp | None = None,
    calendar_name: str = "NYSE",
    tolerance_minutes: float = 150.0,
) -> FreshnessResult:
    target = Path(path)
    if not target.is_file():
        return FreshnessResult(symbol, str(target), 0, None, None, None, False, "DATA_FILE_MISSING")

    frame, _ = read_canonical_parquet(target, verify_hash=False, verify_metadata=False)
    if frame.empty:
        return FreshnessResult(symbol, str(target), 0, None, None, None, False, "DATA_EMPTY")

    latest = _utc(frame.index.max())
    now_ts = _utc(now if now is not None else pd.Timestamp.now(tz="UTC"))
    reference, market_open_now = expected_reference(now_ts, calendar_name)
    if reference is None:
        return FreshnessResult(
            symbol, str(target), len(frame), latest.isoformat(), None, None, False,
            "MARKET_CALENDAR_REFERENCE_MISSING",
        )

    # During an open session, the latest *closed* 1h bar may reasonably trail
    # wall-clock time by up to the configured tolerance. Outside the session,
    # compare against the most recently completed market close.
    age = float((reference - latest).total_seconds() / 60.0)
    passed = age <= float(tolerance_minutes)
    reason = "FRESH" if passed else ("STALE_DURING_SESSION" if market_open_now else "STALE_LAST_SESSION")
    return FreshnessResult(
        symbol=symbol.upper(),
        path=str(target),
        rows=len(frame),
        latest=latest.isoformat(),
        expected_session_close=reference.isoformat(),
        age_from_expected_minutes=age,
        passed=passed,
        reason=reason,
    )
