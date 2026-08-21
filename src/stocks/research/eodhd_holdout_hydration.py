from __future__ import annotations

from datetime import timedelta

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pandas_market_calendars as mcal

from stocks.data.canonical import (
    CanonicalMetadata,
    canonicalize_ohlcv,
    validate_canonical,
    write_canonical_parquet,
)
from stocks.providers.eodhd import (
    EODHD_BASE_URL,
    normalize_intraday_5m,
    provider_symbol,
    utc_timestamp,
)
from stocks.providers.http import ProviderHTTPClient


EODHD_1H_MAX_DAYS = 7200


@dataclass(frozen=True)
class HydrationResult:
    symbol: str
    status: str
    rows: int
    first: str | None
    last: str | None
    split_count: int
    coverage: float
    provider_requests: int
    output: str | None
    reason: str | None
    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "status": self.status,
            "rows": self.rows,
            "first": self.first,
            "last": self.last,
            "split_count": self.split_count,
            "coverage": self.coverage,
            "provider_requests": self.provider_requests,
            "output": self.output,
            "reason": self.reason,
            "execution_authority": self.execution_authority,
            "broker_calls": 0,
            "order_calls": 0,
        }


def load_holdout_config(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = root / "config/generalization_holdout_v1.json"
    import json
    payload = json.loads(path.read_text(encoding="utf-8"))
    symbols = [
        str(value).strip().upper()
        for value in payload.get("symbols", [])
        if str(value).strip()
    ]
    if len(symbols) != len(set(symbols)):
        raise ValueError("holdout contains duplicate symbols")
    if not payload.get("frozen"):
        raise ValueError("generalization holdout must be frozen")
    payload["symbols"] = symbols
    return payload



def _payload_splits(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("splits", "data"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def normalize_splits(payload: Any, symbol: str) -> list[dict[str, Any]]:
    target = provider_symbol(symbol)
    result: list[dict[str, Any]] = []

    for row in _payload_splits(payload):
        code = str(row.get("code") or row.get("symbol") or target).upper()
        if "." not in code:
            code = provider_symbol(code)
        if code != target:
            continue

        raw_date = row.get("split_date") or row.get("date")
        if not raw_date:
            continue

        old_value = pd.to_numeric(
            row.get("old_shares") or row.get("oldShares"), errors="coerce"
        )
        new_value = pd.to_numeric(
            row.get("new_shares") or row.get("newShares"), errors="coerce"
        )

        ratio: float | None = None
        old_number: float | None = None
        new_number: float | None = None

        if (
            not pd.isna(old_value)
            and not pd.isna(new_value)
            and float(old_value) > 0
            and float(new_value) > 0
        ):
            old_number = float(old_value)
            new_number = float(new_value)
            ratio = new_number / old_number

        if ratio is None:
            raw_split = str(row.get("split") or row.get("ratio") or "").strip()
            separator = "/" if "/" in raw_split else ":" if ":" in raw_split else None
            if separator:
                left, right = (part.strip() for part in raw_split.split(separator, 1))
                numerator = pd.to_numeric(left, errors="coerce")
                denominator = pd.to_numeric(right, errors="coerce")
                if (
                    not pd.isna(numerator)
                    and not pd.isna(denominator)
                    and float(numerator) > 0
                    and float(denominator) > 0
                ):
                    new_number = float(numerator)
                    old_number = float(denominator)
                    ratio = new_number / old_number

        if (
            ratio is None
            or old_number is None
            or new_number is None
            or not math.isfinite(ratio)
            or ratio <= 0
        ):
            continue

        result.append(
            {
                "split_date": pd.Timestamp(str(raw_date)).date(),
                "old_shares": old_number,
                "new_shares": new_number,
                "ratio": float(ratio),
            }
        )

    deduplicated: dict[tuple[object, float], dict[str, Any]] = {}
    for row in result:
        key = (row["split_date"], round(float(row["ratio"]), 12))
        deduplicated[key] = row

    return sorted(
        deduplicated.values(),
        key=lambda row: (row["split_date"], row["ratio"]),
    )

def apply_split_adjustments(
    frame: pd.DataFrame,
    splits: Iterable[dict[str, Any]],
    *,
    exchange_timezone: str = "America/New_York",
) -> pd.DataFrame:
    work = canonicalize_ohlcv(frame).copy()
    validate_canonical(work)
    local_dates = pd.Index(work.index.tz_convert(exchange_timezone).date)
    for split in splits:
        split_date = split["split_date"]
        ratio = float(split["ratio"])
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError(f"invalid split ratio: {ratio}")
        mask = local_dates < split_date
        if not bool(mask.any()):
            continue
        for column in ("open", "high", "low", "close"):
            work.loc[mask, column] = (
                pd.to_numeric(work.loc[mask, column], errors="coerce") / ratio
            )
        if "volume" in work:
            work.loc[mask, "volume"] = (
                pd.to_numeric(work.loc[mask, "volume"], errors="coerce") * ratio
            )
    work = canonicalize_ohlcv(work)
    validate_canonical(work)
    return work


def closed_nyse_rth_1h(
    frame: pd.DataFrame,
    *,
    as_of: str | pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = canonicalize_ohlcv(frame)
    validate_canonical(work)
    cutoff = utc_timestamp(as_of)
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=work.index.min().date(),
        end_date=min(work.index.max(), cutoff).date(),
    )
    expected: list[pd.Timestamp] = []
    for _, session in schedule.iterrows():
        market_open = pd.Timestamp(session["market_open"]).tz_convert("UTC")
        market_close = pd.Timestamp(session["market_close"]).tz_convert("UTC")
        cursor = market_open
        while cursor < market_close:
            if cursor <= cutoff:
                expected.append(cursor)
            cursor += timedelta(hours=1)
    expected_index = pd.DatetimeIndex(expected, name="timestamp")
    if expected_index.empty:
        raise ValueError("no expected NYSE RTH 1h buckets")
    result = work.reindex(expected_index)
    required = ["open", "high", "low", "close", "volume"]
    complete = ~result[required].isna().any(axis=1)
    result = result.loc[complete].copy()
    if result.empty:
        raise ValueError("no complete NYSE RTH 1h bars")
    result = canonicalize_ohlcv(result)
    validate_canonical(result)
    coverage = len(result) / len(expected_index)
    return result, {
        "expected_buckets": int(len(expected_index)),
        "actual_buckets": int(len(result)),
        "missing_buckets": int(len(expected_index) - len(result)),
        "coverage": float(coverage),
        "session": "NYSE_RTH",
        "source_interval": "1h",
        "target_interval": "1h",
        "forward_fill": False,
        "fabricated_volume": False,
    }


def quality_audit(frame: pd.DataFrame) -> dict[str, Any]:
    work = canonicalize_ohlcv(frame)
    validate_canonical(work)
    previous_close = pd.to_numeric(work["close"], errors="coerce").shift(1)
    current_open = pd.to_numeric(work["open"], errors="coerce")
    gap = (current_open / previous_close - 1.0).abs().replace(
        [float("inf"), float("-inf")], pd.NA
    ).dropna()
    return {
        "rows": int(len(work)),
        "first": work.index.min().isoformat() if len(work) else None,
        "last": work.index.max().isoformat() if len(work) else None,
        "maximum_absolute_open_gap": float(gap.max()) if not gap.empty else 0.0,
        "duplicate_timestamps": int(work.index.duplicated().sum()),
    }


def _hydration_cutoff(
    as_of: str | pd.Timestamp,
) -> pd.Timestamp:
    if isinstance(as_of, str):
        value = as_of.strip()
        if len(value) == 10 and value[4] == "-" and value[7] == "-":
            start = pd.Timestamp(value, tz="UTC")
            return start + timedelta(days=1) - timedelta(microseconds=1)
    return utc_timestamp(as_of)


def expected_latest_closed_nyse_rth_1h_start(
    as_of: str | pd.Timestamp,
) -> pd.Timestamp:
    cutoff = _hydration_cutoff(as_of)
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=(cutoff - timedelta(days=10)).date(),
        end_date=cutoff.date(),
    )
    candidates: list[pd.Timestamp] = []
    for _, session in schedule.iterrows():
        market_open = pd.Timestamp(session["market_open"]).tz_convert("UTC")
        market_close = pd.Timestamp(session["market_close"]).tz_convert("UTC")
        cursor = market_open
        while cursor < market_close:
            available_at = min(cursor + timedelta(hours=1), market_close)
            if available_at <= cutoff:
                candidates.append(cursor)
            cursor += timedelta(hours=1)
    if not candidates:
        raise ValueError("no closed NYSE RTH 1h bucket available")
    return max(candidates)


def existing_hourly_state(
    project_root: str | Path,
    symbol: str,
    *,
    minimum_rows: int,
    as_of: str | pd.Timestamp,
    maximum_staleness_days: int = 14,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    symbol = symbol.upper()
    expected_last = expected_latest_closed_nyse_rth_1h_start(as_of)
    candidates = (
        root / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet",
        root / "data/adjusted" / f"{symbol}_1h.parquet",
        root / "data/derived" / f"{symbol}_1h.parquet",
        root / "data/processed" / f"{symbol}_1h.parquet",
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            raw = pd.read_parquet(path)
            from stocks.research.strategy_factory_1h import prepare_one_hour_frame
            frame = prepare_one_hour_frame(raw, symbol)
        except Exception as exc:
            return {
                "usable": False,
                "path": str(path),
                "rows": 0,
                "expected_last": expected_last.isoformat(),
                "reason": f"INVALID_EXISTING:{type(exc).__name__}:{exc}",
            }
        if frame.empty:
            return {
                "usable": False,
                "path": str(path),
                "rows": 0,
                "expected_last": expected_last.isoformat(),
                "reason": "EMPTY_EXISTING",
            }
        last = pd.Timestamp(frame["date"].max())
        last = last.tz_localize("UTC") if last.tzinfo is None else last.tz_convert("UTC")
        rows_ok = len(frame) >= int(minimum_rows)
        session_fresh = last == expected_last
        stale_seconds = max((expected_last - last).total_seconds(), 0.0)
        if not rows_ok:
            reason = "INSUFFICIENT_ROWS"
        elif last < expected_last:
            reason = "STALE_EXISTING_LATEST_SESSION_BAR_MISSING"
        elif last > expected_last:
            reason = "EXISTING_DATA_AFTER_EXPECTED_CLOSED_BAR"
        else:
            reason = None
        return {
            "usable": bool(rows_ok and session_fresh),
            "path": str(path),
            "rows": int(len(frame)),
            "last": last.isoformat(),
            "expected_last": expected_last.isoformat(),
            "stale_seconds": float(stale_seconds),
            "stale_days": int(stale_seconds // 86400),
            "session_fresh": bool(session_fresh),
            "reason": reason,
        }
    return {
        "usable": False,
        "path": None,
        "rows": 0,
        "expected_last": expected_last.isoformat(),
        "reason": "MISSING_1H",
    }


def fetch_native_1h(
    symbol: str,
    *,
    start: str | pd.Timestamp,
    end_exclusive: str | pd.Timestamp,
    api_key: str,
    client: ProviderHTTPClient,
) -> pd.DataFrame:
    start_ts = utc_timestamp(start)
    end_ts = utc_timestamp(end_exclusive)
    if start_ts >= end_ts:
        raise ValueError("start must be before end")
    if (end_ts - start_ts).days > EODHD_1H_MAX_DAYS:
        raise ValueError("EODHD 1h request exceeds 7200-day provider limit")
    payload = client.get_json(
        f"{EODHD_BASE_URL}/intraday/{provider_symbol(symbol)}",
        params={
            "api_token": api_key,
            "fmt": "json",
            "interval": "1h",
            "from": int(start_ts.timestamp()),
            "to": int(end_ts.timestamp()) - 1,
        },
    )
    # Existing normalizer validates epoch/OHLCV semantics and is interval-agnostic.
    frame = normalize_intraday_5m(payload)
    return frame.loc[(frame.index >= start_ts) & (frame.index < end_ts)].copy()



def fetch_split_history(
    symbol: str,
    *,
    start: str,
    end: str,
    api_key: str,
    client: ProviderHTTPClient,
) -> list[dict[str, Any]]:
    payload = client.get_json(
        f"{EODHD_BASE_URL}/splits/{provider_symbol(symbol)}",
        params={
            "api_token": api_key,
            "fmt": "json",
            "from": start,
            "to": end,
        },
    )
    return normalize_splits(payload, symbol)

def hydrate_symbol(
    project_root: str | Path,
    symbol: str,
    *,
    start: str,
    as_of: str,
    api_key: str,
    minimum_rows: int,
    minimum_coverage: float,
    client: ProviderHTTPClient,
) -> HydrationResult:
    root = Path(project_root).resolve()
    symbol = symbol.upper()
    existing = existing_hourly_state(
        root, symbol, minimum_rows=minimum_rows, as_of=as_of
    )
    if existing["usable"]:
        return HydrationResult(
            symbol=symbol,
            status="EXISTING_USABLE",
            rows=int(existing["rows"]),
            first=None,
            last=existing.get("last"),
            split_count=0,
            coverage=1.0,
            provider_requests=0,
            output=existing.get("path"),
            reason=None,
        )
    end_exclusive = (
        pd.Timestamp(as_of).normalize() + timedelta(days=1)
    ).strftime("%Y-%m-%d")
    raw = fetch_native_1h(
        symbol,
        start=start,
        end_exclusive=end_exclusive,
        api_key=api_key,
        client=client,
    )
    if raw.empty:
        raise ValueError(f"{symbol}: EODHD returned zero 1h rows")
    splits = fetch_split_history(
        symbol, start=start, end=as_of, api_key=api_key, client=client
    )
    adjusted = apply_split_adjustments(raw, splits)
    rth, session_audit = closed_nyse_rth_1h(
        adjusted, as_of=f"{as_of}T23:59:59Z"
    )
    audit = quality_audit(rth)
    if len(rth) < int(minimum_rows):
        raise ValueError(
            f"{symbol}: only {len(rth)} RTH 1h rows; minimum is {minimum_rows}"
        )
    if float(session_audit["coverage"]) < float(minimum_coverage):
        raise ValueError(
            f"{symbol}: RTH coverage {session_audit['coverage']:.4f} "
            f"< {minimum_coverage:.4f}"
        )
    if int(audit["duplicate_timestamps"]) != 0:
        raise ValueError(f"{symbol}: duplicate timestamps after hydration")
    if float(audit["maximum_absolute_open_gap"]) > 2.0:
        raise ValueError(
            f"{symbol}: extreme post-adjustment overnight gap "
            f"{audit['maximum_absolute_open_gap']:.4f}"
        )
    target = root / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet"
    write_canonical_parquet(
        rth,
        target,
        CanonicalMetadata(
            symbol=symbol,
            exchange="US",
            timeframe="1h",
            source="EODHD_NATIVE_1H_HOLDOUT_HYDRATION",
            adjustment="SPLIT_ADJUSTED_ONLY",
            provenance={
                "provider": "EODHD",
                "provider_symbol": provider_symbol(symbol),
                "interval": "1h",
                "rth_filter": "NYSE_CALENDAR_EXACT_BUCKET_STARTS",
                "split_source": "EODHD_HISTORICAL_SPLITS",
                "split_count": len(splits),
                "current_selection_used": False,
                "execution_authority": "NONE",
            },
        ),
        extra_metadata={"session_audit": session_audit, "quality_audit": audit},
    )
    expected_latest = expected_latest_closed_nyse_rth_1h_start(as_of)
    actual_latest = rth.index.max()
    operationally_fresh = actual_latest == expected_latest
    return HydrationResult(
        symbol=symbol,
        status=(
            "HYDRATED"
            if operationally_fresh
            else "HYDRATED_PROVIDER_LAG"
        ),
        rows=int(len(rth)),
        first=rth.index.min().isoformat(),
        last=actual_latest.isoformat(),
        split_count=int(len(splits)),
        coverage=float(session_audit["coverage"]),
        provider_requests=2,
        output=str(target.resolve()),
        reason=(
            None
            if operationally_fresh
            else "PROVIDER_NOT_FINALIZED_TO_EXPECTED_LATEST_CLOSED_BAR"
        ),
    )
