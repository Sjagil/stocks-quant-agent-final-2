from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv, validate_canonical
from stocks.providers.eodhd import EODHD_BASE_URL, provider_symbol
from stocks.providers.http import ProviderHTTPClient


@dataclass(frozen=True)
class EODHDDailyResult:
    frame: pd.DataFrame
    provider_symbol: str
    request_count: int


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if payload.get("error") or payload.get("message"):
            raise ValueError(f"EODHD EOD error response: {payload}")
    return []


def normalize_eodhd_daily(
    payload: Any,
    *,
    exchange_timezone: str = "America/New_York",
) -> pd.DataFrame:
    rows = _rows(payload)
    if not rows:
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], tz="UTC", name="timestamp"),
        )

    raw = pd.DataFrame(rows)
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"EODHD EOD payload missing fields: {missing}")

    for column in ("open", "high", "low", "close", "volume"):
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    raw = raw.dropna(
        subset=["date", "open", "high", "low", "close", "volume"]
    ).copy()

    if raw.empty:
        raise ValueError("EODHD EOD payload has no valid OHLCV rows")

    # Daily bars represent an exchange session. Store each date at 16:00
    # America/New_York so weekly grouping uses the actual exchange date
    # across DST transitions instead of shifting dates at 00:00 UTC.
    local_close = (
        raw["date"].dt.normalize()
        + pd.Timedelta(hours=16)
    )
    timestamps = (
        pd.DatetimeIndex(local_close)
        .tz_localize(
            exchange_timezone,
            ambiguous="raise",
            nonexistent="raise",
        )
        .tz_convert("UTC")
    )

    frame = pd.DataFrame(
        {
            "open": raw["open"].to_numpy(dtype=float),
            "high": raw["high"].to_numpy(dtype=float),
            "low": raw["low"].to_numpy(dtype=float),
            "close": raw["close"].to_numpy(dtype=float),
            "volume": raw["volume"].to_numpy(dtype=float),
        },
        index=pd.DatetimeIndex(timestamps, name="timestamp"),
    ).sort_index()

    if frame.index.duplicated().any():
        duplicated = frame.loc[frame.index.duplicated(keep=False)]
        if duplicated.nunique(dropna=False).max() > 1:
            raise ValueError("conflicting duplicate EODHD daily bars")
        frame = frame.loc[~frame.index.duplicated(keep="last")]

    frame = canonicalize_ohlcv(frame)
    validate_canonical(frame)
    return frame


def fetch_eodhd_daily(
    symbol: str,
    *,
    start: str,
    end: str,
    api_key: str,
    client: ProviderHTTPClient,
) -> EODHDDailyResult:
    if not str(api_key).strip():
        raise ValueError("EODHD API key is required")

    ticker = provider_symbol(symbol)
    payload = client.get_json(
        f"{EODHD_BASE_URL}/eod/{ticker}",
        params={
            "api_token": api_key,
            "fmt": "json",
            "period": "d",
            "order": "a",
            "from": str(start),
            "to": str(end),
        },
    )
    frame = normalize_eodhd_daily(payload)
    return EODHDDailyResult(
        frame=frame,
        provider_symbol=ticker,
        request_count=1,
    )
