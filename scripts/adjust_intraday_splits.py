from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx
import pandas as pd

from stocks.data import (
    CanonicalMetadata,
    apply_split_adjustments,
    read_canonical_parquet,
    split_events_from_payload,
    write_canonical_parquet,
)

BASE_URL = "https://eodhd.com/api"


def load_local_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_splits(token: str, ticker: str, start: str, end: str) -> list[dict]:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(
            f"{BASE_URL}/splits/{ticker}",
            params={"api_token": token, "fmt": "json", "from": start, "to": end},
        )
        response.raise_for_status()
        payload = response.json()
    if isinstance(payload, dict):
        payload = payload.get("splits") or payload.get("data") or payload
    if not isinstance(payload, list):
        raise RuntimeError(f"unexpected EODHD split payload for {ticker}: {payload}")
    return [dict(item) for item in payload]


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Apply explicit EODHD stock-split normalization to canonical OHLCV")
    parser.add_argument("parquet", type=Path)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/adjusted"))
    parser.add_argument("--force", action="store_true", help="Allow re-adjusting input whose canonical metadata is already non-raw")
    args = parser.parse_args()

    token = os.environ.get("EODHD_API_KEY", "").strip()
    if not token:
        raise SystemExit("ERROR: EODHD_API_KEY missing from .env")
    frame, source_meta = read_canonical_parquet(args.parquet)
    existing_adjustment = str((source_meta or {}).get("adjustment") or "raw")
    if existing_adjustment != "raw" and not args.force:
        raise SystemExit(
            f"ERROR: input metadata says adjustment={existing_adjustment!r}; refusing possible double adjustment. "
            "Use a raw/processed parquet, or pass --force only if this is intentional."
        )
    start = frame.index.min().date().isoformat()
    end = pd.Timestamp.now(tz="UTC").date().isoformat()
    raw_events = fetch_splits(token, args.ticker, start, end)
    events = split_events_from_payload(raw_events)
    print(f"SPLITS ticker={args.ticker} count={len(events)}")
    for event in events:
        affected = int((frame.index < event.effective_at).sum())
        print(f"APPLY split_date={event.effective_at.date()} factor={event.factor:g} bars_affected={affected}")
    adjusted = apply_split_adjustments(frame, events)
    output = args.output_dir / args.parquet.name
    short_symbol = args.ticker.split(".")[0].upper()
    timeframe = str((source_meta or {}).get("timeframe") or args.parquet.stem.rsplit("_", 1)[-1])
    target, metadata_path = write_canonical_parquet(
        adjusted,
        output,
        CanonicalMetadata(
            symbol=short_symbol,
            exchange=args.ticker.split(".", 1)[1] if "." in args.ticker else None,
            timeframe=timeframe,
            source="EODHD",
            adjustment="split_adjusted_latest_share_basis",
            provenance={"source_path": str(args.parquet), "ticker": args.ticker},
        ),
        extra_metadata={
            "corporate_action_policy": "split_only; dividends remain explicit cashflows",
            "splits": [
                {"effective_at": event.effective_at.isoformat(), "factor": event.factor, "raw": event.source_payload}
                for event in events
            ],
        },
    )
    corporate_path = target.with_suffix(".corporate_actions.json")
    corporate_path.write_text(
        json.dumps(
            {
                "ticker": args.ticker,
                "policy": "split_only",
                "events": [
                    {"effective_at": event.effective_at.isoformat(), "factor": event.factor, "raw": event.source_payload}
                    for event in events
                ],
                "canonical_metadata": str(metadata_path),
            },
            indent=2,
            sort_keys=True,
            default=str,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"SAVED={target}")
    print(f"METADATA={metadata_path}")
    print(f"CORPORATE_ACTIONS={corporate_path}")


if __name__ == "__main__":
    main()
