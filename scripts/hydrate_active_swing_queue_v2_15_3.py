#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from stocks.data.canonical import CanonicalMetadata, write_canonical_parquet
from stocks.data.eodhd_5m_source import collect_eodhd_5m_15m
from stocks.data.eodhd_daily_source import fetch_eodhd_daily
from stocks.data.multitimeframe import (
    ACTIVE_SWING_TIMEFRAMES,
    load_active_swing_bundle,
    materialize_bundle,
)
from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.research.eodhd_holdout_hydration import (
    apply_split_adjustments,
    fetch_split_history,
)

ROOT = Path(__file__).resolve().parents[1]


def _queue_symbols(limit: int) -> list[str]:
    path = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_training_queue_v2_13/queue.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(
            "agent training queue missing; build v2.13 queue first"
        )
    frame = pd.read_csv(path)
    if "symbol" not in frame:
        raise ValueError("agent training queue missing symbol column")
    return [
        str(value).strip().upper()
        for value in frame["symbol"].head(max(1, int(limit)))
        if str(value).strip()
    ]


def _canonical_from_15m_storage(path: Path) -> pd.DataFrame:
    raw = pd.read_parquet(path)
    time_col = (
        "timestamp_utc"
        if "timestamp_utc" in raw
        else "timestamp"
        if "timestamp" in raw
        else None
    )
    if time_col is None:
        raise ValueError(f"{path}: timestamp column missing")
    frame = raw[
        [time_col, "open", "high", "low", "close", "volume"]
    ].copy()
    frame[time_col] = pd.to_datetime(frame[time_col], utc=True)
    frame = frame.set_index(time_col)
    frame.index.name = "timestamp"
    return frame


def _write_15m(
    symbol: str,
    *,
    start: str,
    as_of: str,
    api_key: str,
    client: ProviderHTTPClient,
    chunk_days: int,
) -> dict[str, Any]:
    result = collect_eodhd_5m_15m(
        ROOT,
        symbols=[symbol],
        start=start,
        end=as_of,
        as_of=f"{as_of}T23:59:59Z",
        chunk_days=int(chunk_days),
    )
    source = Path(result["bars"][0]["path"])
    raw = _canonical_from_15m_storage(source)
    splits = fetch_split_history(
        symbol,
        start=start,
        end=as_of,
        api_key=api_key,
        client=client,
    )
    adjusted = apply_split_adjustments(raw, splits)

    target = (
        ROOT
        / "data/canonical/provider_fabric"
        / f"{symbol}_15m.parquet"
    )
    write_canonical_parquet(
        adjusted,
        target,
        CanonicalMetadata(
            symbol=symbol,
            exchange="US",
            timeframe="15m",
            source="EODHD_NATIVE_5M_DERIVED_15M_ACTIVE_SWING_V2_15_3",
            adjustment="SPLIT_ADJUSTED_ONLY",
            provenance={
                "provider": "EODHD",
                "source_interval": "5m",
                "target_interval": "15m",
                "aggregation": "EXACT_3X5M_SESSION_GRID",
                "split_count": len(splits),
                "forward_fill": False,
                "provider_averaging": False,
                "execution_authority": "NONE",
            },
        ),
    )
    return {
        "path": str(target),
        "rows": int(len(adjusted)),
        "split_count": int(len(splits)),
        "provider_calls": int(result["provider_calls"]),
    }


def _write_1d(
    symbol: str,
    *,
    start: str,
    as_of: str,
    api_key: str,
    client: ProviderHTTPClient,
) -> dict[str, Any]:
    fetched = fetch_eodhd_daily(
        symbol,
        start=start,
        end=as_of,
        api_key=api_key,
        client=client,
    )
    if fetched.frame.empty:
        raise ValueError(f"{symbol}: zero EODHD daily rows")

    splits = fetch_split_history(
        symbol,
        start=start,
        end=as_of,
        api_key=api_key,
        client=client,
    )
    adjusted = apply_split_adjustments(
        fetched.frame,
        splits,
    )

    target = ROOT / "data/processed" / f"{symbol}_1d.parquet"
    write_canonical_parquet(
        adjusted,
        target,
        CanonicalMetadata(
            symbol=symbol,
            exchange="US",
            timeframe="1d",
            source="EODHD_EOD_ACTIVE_SWING_V2_15_3",
            adjustment="SPLIT_ADJUSTED_ONLY",
            provenance={
                "provider": "EODHD",
                "endpoint": "/eod/{ticker}",
                "period": "d",
                "split_count": len(splits),
                "adjusted_close_used": False,
                "forward_fill": False,
                "execution_authority": "NONE",
            },
        ),
    )
    return {
        "path": str(target),
        "rows": int(len(adjusted)),
        "split_count": int(len(splits)),
        "provider_calls": int(fetched.request_count),
    }


def _existing(root: Path, symbol: str, timeframe: str) -> Path | None:
    candidates = {
        "15m": (
            root / "data/canonical/provider_fabric" / f"{symbol}_15m.parquet",
            root / "data/canonical/split_adjusted" / f"{symbol}_15m.parquet",
            root / "data/derived" / f"{symbol}_15m.parquet",
        ),
        "1d": (
            root / "data/processed" / f"{symbol}_1d.parquet",
            root / "data/adjusted" / f"{symbol}_1d.parquet",
            root / "data/derived" / f"{symbol}_1d.parquet",
        ),
    }
    return next(
        (path for path in candidates.get(timeframe, ()) if path.is_file()),
        None,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--start")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(
        (
            ROOT / "config/active_swing_hydration_v2_15_3.yaml"
        ).read_text(encoding="utf-8")
    )
    start = str(args.start or config["start"])
    as_of = str(args.as_of)

    if args.symbols:
        symbols = [
            value.strip().upper()
            for value in args.symbols.split(",")
            if value.strip()
        ]
    else:
        symbols = _queue_symbols(args.limit)

    if not symbols:
        raise SystemExit("no symbols resolved")

    load_project_env(ROOT)
    api_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )
    if not api_key:
        raise SystemExit("EODHD API key is not configured")

    minimum_rows = {
        str(key): int(value)
        for key, value in config["minimum_rows"].items()
    }
    chunk_days = int(config["intraday"]["chunk_days"])

    rows: list[dict[str, Any]] = []
    provider_calls = 0

    with ProviderHTTPClient(
        user_agent="stocks-quant-agent/active-swing-hydration-v2.15.3"
    ) as client:
        for symbol in symbols:
            row: dict[str, Any] = {
                "symbol": symbol,
                "status": "PENDING",
                "15m_action": None,
                "1d_action": None,
                "failure": None,
            }
            try:
                existing_15m = _existing(ROOT, symbol, "15m")
                if existing_15m is None or args.force:
                    result_15m = _write_15m(
                        symbol,
                        start=start,
                        as_of=as_of,
                        api_key=api_key,
                        client=client,
                        chunk_days=chunk_days,
                    )
                    row["15m_action"] = "HYDRATED"
                    provider_calls += int(result_15m["provider_calls"])
                else:
                    row["15m_action"] = "EXISTING"

                existing_1d = _existing(ROOT, symbol, "1d")
                if existing_1d is None or args.force:
                    result_1d = _write_1d(
                        symbol,
                        start=start,
                        as_of=as_of,
                        api_key=api_key,
                        client=client,
                    )
                    row["1d_action"] = "HYDRATED"
                    provider_calls += int(result_1d["provider_calls"])
                else:
                    row["1d_action"] = "EXISTING"

                bundle = load_active_swing_bundle(ROOT, symbol)
                materialized = materialize_bundle(ROOT, bundle)

                missing = [
                    tf
                    for tf in ACTIVE_SWING_TIMEFRAMES
                    if tf not in bundle.frames
                ]
                counts = {
                    tf: int(len(bundle.frames.get(tf, [])))
                    for tf in ACTIVE_SWING_TIMEFRAMES
                }
                insufficient = [
                    tf
                    for tf in ACTIVE_SWING_TIMEFRAMES
                    if counts[tf] < minimum_rows[tf]
                ]

                row.update(
                    {
                        **{f"rows_{tf}": counts[tf] for tf in ACTIVE_SWING_TIMEFRAMES},
                        "missing": "|".join(missing),
                        "insufficient": "|".join(insufficient),
                        "materialized": "|".join(sorted(materialized)),
                    }
                )

                if missing:
                    raise ValueError(f"MISSING_TIMEFRAMES:{'|'.join(missing)}")
                if insufficient:
                    raise ValueError(
                        f"INSUFFICIENT_ROWS:{'|'.join(insufficient)}"
                    )

                row["status"] = "READY"
                print(
                    "ACTIVE_SWING_READY",
                    symbol,
                    "15M",
                    counts["15m"],
                    "1H",
                    counts["1h"],
                    "2H",
                    counts["2h"],
                    "4H",
                    counts["4h"],
                    "1D",
                    counts["1d"],
                    "1W",
                    counts["1w"],
                )

            except Exception as exc:
                row["status"] = "FAILED"
                row["failure"] = f"{type(exc).__name__}:{exc}"
                print(
                    "ACTIVE_SWING_HYDRATION_FAILED",
                    symbol,
                    row["failure"],
                )

            rows.append(row)

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "active_swing_hydration_v2_15_3"
    )
    output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "results.csv", index=False)

    ready = int((frame["status"] == "READY").sum())
    audit = {
        "schema": "active_swing_hydration_audit_v2_15_3",
        "symbols": symbols,
        "ready": ready,
        "failed": int(len(frame) - ready),
        "provider_calls": int(provider_calls),
        "required_timeframes": list(ACTIVE_SWING_TIMEFRAMES),
        "timeframe_chain": (
            "1W_REGIME->1D_REGIME->4H_2H_SETUP->"
            "1H_SIGNAL->15M_EXECUTION"
        ),
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "ACTIVE_SWING_HYDRATION_V2_15_3",
        "REQUESTED",
        len(frame),
        "READY",
        ready,
        "FAILED",
        len(frame) - ready,
        "PROVIDER_CALLS",
        provider_calls,
    )
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0 if ready == len(frame) else 2


if __name__ == "__main__":
    raise SystemExit(main())
