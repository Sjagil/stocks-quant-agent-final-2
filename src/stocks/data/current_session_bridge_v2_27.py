from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    merge_canonical_frames,
    read_canonical_parquet,
    validate_canonical,
    write_canonical_parquet,
)
from stocks.research.eodhd_holdout_hydration import (
    expected_latest_closed_nyse_rth_1h_start,
)

SCHEMA = "current_session_market_bridge_v2_27"
AUTHORITY_NONE = "NONE"


def _utc(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    return result.tz_localize("UTC") if result.tzinfo is None else result.tz_convert("UTC")


def _nyse_schedule(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    calendar = mcal.get_calendar("NYSE")
    return calendar.schedule(start_date=start.date(), end_date=end.date())


def latest_completed_nyse_session_v227(
    decision_time: datetime | pd.Timestamp,
) -> str:
    now = _utc(decision_time)
    schedule = _nyse_schedule(now - timedelta(days=14), now)
    closes = pd.to_datetime(schedule["market_close"], utc=True)
    completed = schedule.loc[closes <= now]
    if completed.empty:
        raise ValueError("NO_COMPLETED_NYSE_SESSION_IN_LOOKBACK")
    return pd.Timestamp(completed.index[-1]).date().isoformat()


def expected_closed_nyse_1h_starts_v227(
    decision_time: datetime | pd.Timestamp,
    *,
    start_date: pd.Timestamp | None = None,
) -> pd.DatetimeIndex:
    now = _utc(decision_time)
    first = _utc(start_date) if start_date is not None else now - timedelta(days=10)
    schedule = _nyse_schedule(first, now)
    starts: list[pd.Timestamp] = []
    for _, row in schedule.iterrows():
        market_open = _utc(row["market_open"])
        market_close = _utc(row["market_close"])
        cursor = market_open
        while cursor < market_close:
            available_at = min(cursor + timedelta(hours=1), market_close)
            if available_at <= now:
                starts.append(cursor)
            cursor += timedelta(hours=1)
    return pd.DatetimeIndex(starts, name="timestamp")


def _records_frame(records: Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    rows = [dict(row) for row in records]
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError("IBKR_RECORD_COLUMNS_MISSING:" + ",".join(missing))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError("IBKR_RECORD_TIMESTAMP_INVALID")
    frame = frame.set_index("timestamp").sort_index()
    return canonicalize_ohlcv(
        frame,
        drop_duplicate_timestamps=True,
        drop_missing_required=True,
    )


def aggregate_ibkr_30m_to_nyse_1h_v227(
    records: Iterable[Mapping[str, Any]],
    *,
    decision_time: datetime | pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    now = _utc(decision_time)
    raw = _records_frame(records)
    if raw.empty:
        raise ValueError("IBKR_30M_EMPTY")

    schedule = _nyse_schedule(raw.index.min() - timedelta(days=1), now)
    expected_closed: set[pd.Timestamp] = set()
    bucket_map: dict[pd.Timestamp, pd.Timestamp] = {}
    bucket_expected: dict[pd.Timestamp, list[pd.Timestamp]] = {}

    for _, row in schedule.iterrows():
        market_open = _utc(row["market_open"])
        market_close = _utc(row["market_close"])
        cursor = market_open
        while cursor < market_close:
            end = min(cursor + timedelta(minutes=30), market_close)
            if end <= now:
                expected_closed.add(cursor)
                bucket_number = int((cursor - market_open).total_seconds() // 3600)
                bucket = market_open + timedelta(hours=bucket_number)
                bucket_map[cursor] = bucket
                bucket_expected.setdefault(bucket, []).append(cursor)
            cursor += timedelta(minutes=30)

    accepted = raw.loc[raw.index.isin(expected_closed)].copy()
    if accepted.empty:
        raise ValueError("IBKR_30M_NO_CLOSED_RTH_ROWS")
    accepted["_bucket"] = [bucket_map[index] for index in accepted.index]

    rows: list[dict[str, Any]] = []
    incomplete_buckets: list[str] = []
    for bucket, expected in sorted(bucket_expected.items()):
        present = accepted.loc[accepted["_bucket"] == bucket].drop(columns=["_bucket"])
        expected_set = set(expected)
        present_set = set(present.index)
        if not expected_set.issubset(present_set):
            if present_set:
                incomplete_buckets.append(bucket.isoformat())
            continue
        present = present.loc[sorted(expected_set)]
        rows.append(
            {
                "timestamp": bucket,
                "open": float(present["open"].iloc[0]),
                "high": float(present["high"].max()),
                "low": float(present["low"].min()),
                "close": float(present["close"].iloc[-1]),
                "volume": float(present["volume"].sum()),
            }
        )

    if not rows:
        raise ValueError("IBKR_30M_NO_COMPLETE_1H_BUCKETS")

    hourly = canonicalize_ohlcv(
        pd.DataFrame(rows),
        drop_duplicate_timestamps=True,
        drop_missing_required=True,
    )
    validate_canonical(hourly)
    return hourly, {
        "schema": "ibkr_30m_to_nyse_1h_v2_27",
        "decision_time": now.isoformat(),
        "raw_rows": int(len(raw)),
        "accepted_closed_rth_30m_rows": int(len(accepted)),
        "hourly_rows": int(len(hourly)),
        "first_hourly": hourly.index.min().isoformat(),
        "last_hourly": hourly.index.max().isoformat(),
        "incomplete_bucket_count": int(len(incomplete_buckets)),
        "incomplete_buckets": incomplete_buckets,
        "forward_fill": False,
        "open_bar_included": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_write_calls": 0,
        "order_calls": 0,
    }


def _relative_difference(left: float, right: float) -> float:
    scale = max(abs(float(left)), abs(float(right)), 1e-12)
    return abs(float(left) - float(right)) / scale


def reconcile_overlap_v227(
    historical: pd.DataFrame,
    ibkr_hourly: pd.DataFrame,
    *,
    price_tolerance_bps: float = 75.0,
    volume_relative_tolerance: float = 0.60,
) -> dict[str, Any]:
    left = canonicalize_ohlcv(historical)
    right = canonicalize_ohlcv(ibkr_hourly)
    overlap = left.index.intersection(right.index)
    if overlap.empty:
        return {"overlap_rows": 0, "passed": False, "reason": "NO_SOURCE_OVERLAP"}

    checked = overlap[-min(4, len(overlap)) :]
    price_limit = float(price_tolerance_bps) / 10_000.0
    failures: list[str] = []
    worst_price = 0.0
    worst_volume = 0.0
    for timestamp in checked:
        for column in ("open", "high", "low", "close"):
            diff = _relative_difference(left.at[timestamp, column], right.at[timestamp, column])
            worst_price = max(worst_price, diff)
            if diff > price_limit:
                failures.append(f"{timestamp.isoformat()}:{column}")
        volume_diff = _relative_difference(
            left.at[timestamp, "volume"], right.at[timestamp, "volume"]
        )
        worst_volume = max(worst_volume, volume_diff)
        if volume_diff > float(volume_relative_tolerance):
            failures.append(f"{timestamp.isoformat()}:volume")

    return {
        "overlap_rows": int(len(overlap)),
        "checked_rows": int(len(checked)),
        "passed": not failures,
        "price_tolerance_bps": float(price_tolerance_bps),
        "volume_relative_tolerance": float(volume_relative_tolerance),
        "worst_price_relative_difference": float(worst_price),
        "worst_volume_relative_difference": float(worst_volume),
        "failures": failures,
        "reason": None if not failures else "SOURCE_OVERLAP_DIVERGENCE",
    }



def canonical_freshness_v227(
    project_root: str | Path,
    symbol: str,
    *,
    decision_time: datetime | pd.Timestamp,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    symbol = str(symbol).strip().upper()
    target = root / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet"
    expected_latest = expected_latest_closed_nyse_rth_1h_start(decision_time)

    if not target.is_file():
        return {
            "symbol": symbol,
            "status": "BLOCKED",
            "operationally_fresh": False,
            "blockers": ["HISTORICAL_CANONICAL_MISSING"],
            "expected_latest": expected_latest.isoformat(),
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    historical, _ = read_canonical_parquet(
        target,
        verify_hash=False,
        verify_metadata=False,
    )
    historical = canonicalize_ohlcv(historical)
    if historical.empty:
        return {
            "symbol": symbol,
            "status": "BLOCKED",
            "operationally_fresh": False,
            "blockers": ["HISTORICAL_CANONICAL_EMPTY"],
            "expected_latest": expected_latest.isoformat(),
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    historical_last = historical.index.max()
    if historical_last > expected_latest:
        return {
            "symbol": symbol,
            "status": "BLOCKED",
            "operationally_fresh": False,
            "blockers": ["HISTORICAL_DATA_FROM_FUTURE_SESSION"],
            "historical_last": historical_last.isoformat(),
            "expected_latest": expected_latest.isoformat(),
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    if historical_last == expected_latest:
        return {
            "symbol": symbol,
            "status": "ALREADY_FRESH",
            "operationally_fresh": True,
            "historical_last": historical_last.isoformat(),
            "expected_latest": expected_latest.isoformat(),
            "appended_rows": 0,
            "ibkr_tail_required": False,
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    return {
        "symbol": symbol,
        "status": "NEEDS_IBKR_TAIL",
        "operationally_fresh": False,
        "historical_last": historical_last.isoformat(),
        "expected_latest": expected_latest.isoformat(),
        "ibkr_tail_required": True,
        "execution_authority": AUTHORITY_NONE,
        "broker_write_calls": 0,
        "order_calls": 0,
    }


def bridge_symbol_v227(
    project_root: str | Path,
    symbol: str,
    records: Iterable[Mapping[str, Any]],
    *,
    decision_time: datetime | pd.Timestamp,
    price_tolerance_bps: float = 75.0,
    volume_relative_tolerance: float = 0.60,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    symbol = str(symbol).strip().upper()
    freshness = canonical_freshness_v227(
        root,
        symbol,
        decision_time=decision_time,
    )
    if freshness["status"] != "NEEDS_IBKR_TAIL":
        return freshness

    target = root / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet"
    historical, historical_meta = read_canonical_parquet(
        target, verify_hash=False, verify_metadata=False
    )
    expected_latest = expected_latest_closed_nyse_rth_1h_start(decision_time)
    historical_last = historical.index.max()

    ibkr_hourly, aggregation_audit = aggregate_ibkr_30m_to_nyse_1h_v227(
        records, decision_time=decision_time
    )

    overlap = reconcile_overlap_v227(
        historical,
        ibkr_hourly,
        price_tolerance_bps=price_tolerance_bps,
        volume_relative_tolerance=volume_relative_tolerance,
    )
    if not overlap["passed"]:
        return {
            "symbol": symbol,
            "status": "BLOCKED",
            "blockers": [str(overlap["reason"])],
            "overlap": overlap,
            "historical_last": historical_last.isoformat(),
            "expected_latest": expected_latest.isoformat(),
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    expected_tail = expected_closed_nyse_1h_starts_v227(
        decision_time, start_date=historical_last
    )
    expected_tail = expected_tail[
        (expected_tail > historical_last) & (expected_tail <= expected_latest)
    ]
    missing = expected_tail.difference(ibkr_hourly.index)
    if len(missing):
        return {
            "symbol": symbol,
            "status": "BLOCKED",
            "blockers": ["IBKR_CURRENT_SESSION_TAIL_INCOMPLETE"],
            "missing_tail_bars": [value.isoformat() for value in missing],
            "historical_last": historical_last.isoformat(),
            "ibkr_last": ibkr_hourly.index.max().isoformat(),
            "expected_latest": expected_latest.isoformat(),
            "overlap": overlap,
            "aggregation": aggregation_audit,
            "execution_authority": AUTHORITY_NONE,
            "broker_write_calls": 0,
            "order_calls": 0,
        }

    tail = ibkr_hourly.loc[expected_tail].copy()
    merged = merge_canonical_frames([historical, tail])
    if merged.index.max() != expected_latest:
        raise RuntimeError("MERGED_SERIES_NOT_OPERATIONALLY_FRESH")

    source_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    write_canonical_parquet(
        merged,
        target,
        CanonicalMetadata(
            symbol=symbol,
            timeframe="1h",
            source="EODHD_HISTORY_PLUS_IBKR_READ_ONLY_CURRENT_SESSION",
            exchange="US",
            currency=(historical_meta or {}).get("currency") or "USD",
            adjustment=(historical_meta or {}).get("adjustment") or "SPLIT_ADJUSTED_ONLY",
            provenance={
                "historical_provider": "EODHD",
                "tail_provider": "IBKR",
                "tail_request": "reqHistoricalData",
                "tail_source_interval": "30m",
                "target_interval": "1h",
                "use_rth": True,
                "keep_up_to_date": False,
                "forward_fill": False,
                "open_bar_included": False,
                "previous_canonical_sha256": source_hash,
                "execution_authority": AUTHORITY_NONE,
            },
        ),
        extra_metadata={
            "bridge_schema": SCHEMA,
            "bridge_decision_time": _utc(decision_time).isoformat(),
            "expected_latest_closed_1h_bar": expected_latest.isoformat(),
            "historical_last_before_bridge": historical_last.isoformat(),
            "appended_rows": int(len(tail)),
            "overlap": overlap,
            "aggregation": aggregation_audit,
        },
    )
    return {
        "symbol": symbol,
        "status": "BRIDGED_FRESH",
        "operationally_fresh": True,
        "historical_last_before_bridge": historical_last.isoformat(),
        "latest_after_bridge": merged.index.max().isoformat(),
        "expected_latest": expected_latest.isoformat(),
        "appended_rows": int(len(tail)),
        "overlap": overlap,
        "aggregation": aggregation_audit,
        "execution_authority": AUTHORITY_NONE,
        "broker_write_calls": 0,
        "order_calls": 0,
    }


def write_bridge_audit_v227(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return target
