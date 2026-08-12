from __future__ import annotations

import argparse
import os
from pathlib import Path

import httpx
import pandas as pd

from stocks.data import CanonicalMetadata, merge_canonical_frames, write_canonical_parquet

BASE_URL = "https://eodhd.com/api"
INTRADAY_MAX_DAYS = {"1m": 120, "5m": 600, "1h": 7200}


def load_local_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ticker_for(symbol: str, exchange: str) -> str:
    normalized = symbol.strip().upper()
    return normalized if "." in normalized else f"{normalized}.{exchange.upper()}"


def request_intraday_chunk(
    client: httpx.Client,
    token: str,
    ticker: str,
    interval: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    response = client.get(
        f"{BASE_URL}/intraday/{ticker}",
        params={
            "api_token": token,
            "interval": interval,
            "fmt": "json",
            "from": int(start.timestamp()),
            "to": int(end.timestamp()),
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"{ticker}: unexpected EODHD payload: {payload}")
    if not payload:
        return pd.DataFrame()
    frame = pd.DataFrame(payload)
    if "timestamp" not in frame.columns:
        raise ValueError(f"{ticker}: timestamp missing from intraday payload")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
    return frame.set_index("timestamp")


def request_eod(
    client: httpx.Client,
    token: str,
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    response = client.get(
        f"{BASE_URL}/eod/{ticker}",
        params={
            "api_token": token,
            "fmt": "json",
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "period": "d",
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"{ticker}: unexpected EODHD payload: {payload}")
    if not payload:
        return pd.DataFrame()
    frame = pd.DataFrame(payload)
    if "date" not in frame.columns:
        raise ValueError(f"{ticker}: date missing from EOD payload")
    frame["timestamp"] = pd.to_datetime(frame["date"], utc=True)
    return frame.set_index("timestamp")


def download(
    token: str,
    ticker: str,
    timeframe: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.DataFrame, int]:
    chunks: list[pd.DataFrame] = []
    requests = 0
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        if timeframe == "1d":
            chunks.append(request_eod(client, token, ticker, start, end))
            requests = 1
        else:
            max_days = INTRADAY_MAX_DAYS[timeframe]
            cursor = start
            while cursor < end:
                chunk_end = min(cursor + pd.Timedelta(days=max_days), end)
                print(f"FETCH {ticker} {timeframe} {cursor.isoformat()} -> {chunk_end.isoformat()}")
                chunks.append(request_intraday_chunk(client, token, ticker, timeframe, cursor, chunk_end))
                requests += 1
                cursor = chunk_end + pd.Timedelta(seconds=1)
    merged = merge_canonical_frames(chunks)
    if merged.empty:
        raise ValueError(f"{ticker}: no market data returned")
    return merged, requests


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Download EODHD data into the canonical OHLCV schema")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--exchange", default="US")
    parser.add_argument("--timeframe", choices=["1m", "5m", "1h", "1d"], default="1h")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    token = os.environ.get("EODHD_API_KEY", "").strip()
    if not token:
        raise SystemExit("ERROR: EODHD_API_KEY is missing from .env")
    start = pd.Timestamp(args.start)
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = pd.Timestamp(args.end) if args.end else pd.Timestamp.now(tz="UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    if end <= start:
        raise SystemExit("ERROR: --end must be after --start")

    failures = 0
    for symbol in args.symbols:
        ticker = ticker_for(symbol, args.exchange)
        short_symbol = ticker.split(".")[0]
        try:
            frame, request_count = download(token, ticker, args.timeframe, start, end)
            output = args.output_dir / f"{short_symbol}_{args.timeframe}.parquet"
            write_canonical_parquet(
                frame,
                output,
                CanonicalMetadata(
                    symbol=short_symbol,
                    exchange=args.exchange.upper(),
                    timeframe=args.timeframe,
                    source="EODHD",
                    adjustment="raw",
                    provenance={"ticker": ticker, "endpoint": "eod" if args.timeframe == "1d" else "intraday"},
                ),
                extra_metadata={"request_count": request_count},
            )
            print(f"SAVED {ticker} rows={len(frame)} start={frame.index.min()} end={frame.index.max()} path={output}")
        except Exception as exc:
            failures += 1
            print(f"FAILED {ticker}: {type(exc).__name__}: {exc}")
    if failures == len(args.symbols):
        raise SystemExit(2)
    if failures:
        print(f"PARTIAL_SUCCESS failed={failures} succeeded={len(args.symbols)-failures}")


if __name__ == "__main__":
    main()
