from __future__ import annotations

import importlib.util
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import (
    CanonicalMetadata,
    merge_canonical_frames,
    read_canonical_parquet,
    write_canonical_parquet,
)
from .freshness_v2_41 import check_file_freshness


def _load_download_module(root: Path):
    path = root / "scripts/download_market_data.py"
    spec = importlib.util.spec_from_file_location("_download_market_data_v241", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _metadata_from_existing(symbol: str, timeframe: str, exchange: str, prior: dict[str, Any] | None):
    prior = prior or {}
    return CanonicalMetadata(
        symbol=symbol.upper(),
        timeframe=timeframe,
        source=str(prior.get("source") or "EODHD"),
        exchange=str(prior.get("exchange") or exchange).upper(),
        asset_type=prior.get("asset_type"),
        currency=prior.get("currency"),
        adjustment=str(prior.get("adjustment") or "raw"),
        provenance={
            **(prior.get("provenance") or {}),
            "incremental_refresh_v2_41": True,
            "provider_rows_are_not_filled": True,
        },
    )


def refresh_provider_fabric(root: str | Path, cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    data_cfg = cfg["data"]
    out_root = root / data_cfg["provider_root"]
    out_root.mkdir(parents=True, exist_ok=True)

    mod = _load_download_module(root)
    mod.load_local_env(root / ".env")
    token = os.environ.get("EODHD_API_KEY", "").strip()
    if not token:
        return {
            "status": "BLOCKED",
            "reason": "EODHD_API_KEY_MISSING",
            "symbols": [],
        }

    now = pd.Timestamp.now(tz="UTC")
    end = now
    period = pd.Timedelta(hours=1 if data_cfg["timeframe"] == "1h" else 0)
    close_lag = pd.Timedelta(seconds=int(data_cfg.get("bar_close_lag_seconds", 120)))
    closed_cutoff = now - close_lag
    results = []
    failures = 0

    for symbol in data_cfg["symbols"]:
        symbol = str(symbol).upper()
        target = out_root / f"{symbol}_{data_cfg['timeframe']}.parquet"
        prior_frame = pd.DataFrame()
        prior_meta = None
        if target.is_file():
            try:
                prior_frame, prior_meta = read_canonical_parquet(
                    target, verify_hash=False, verify_metadata=False
                )
            except Exception as exc:
                results.append({"symbol": symbol, "status": "FAILED", "reason": f"EXISTING_DATA_INVALID:{type(exc).__name__}:{exc}"})
                failures += 1
                continue

        if not prior_frame.empty:
            start = prior_frame.index.max() - pd.Timedelta(days=int(data_cfg.get("overlap_days", 5)))
        else:
            start = now - pd.Timedelta(days=int(data_cfg.get("bootstrap_days", 3650)))

        try:
            new_frame, request_count, audits = mod.download(
                token,
                mod.ticker_for(symbol, data_cfg["exchange"]),
                data_cfg["timeframe"],
                pd.Timestamp(start),
                pd.Timestamp(end),
                max_drop_fraction=float(data_cfg.get("max_drop_fraction", 0.02)),
                quarantine_dir=out_root.parent / "quarantine" / "eodhd",
            )
            if period > pd.Timedelta(0):
                new_frame = new_frame.loc[(new_frame.index + period) <= closed_cutoff]
            merged = merge_canonical_frames([prior_frame, new_frame])
            meta = _metadata_from_existing(symbol, data_cfg["timeframe"], data_cfg["exchange"], prior_meta)
            write_canonical_parquet(
                merged,
                target,
                meta,
                extra_metadata={
                    "incremental_refresh": True,
                    "refresh_requests": int(request_count),
                    "provider_quality": audits,
                    "closed_bar_cutoff": closed_cutoff.isoformat(),
                },
            )
            fresh = check_file_freshness(
                symbol,
                target,
                now=now,
                calendar_name=data_cfg.get("market_calendar", "NYSE"),
                tolerance_minutes=float(data_cfg.get("freshness_tolerance_minutes", 150)),
            )
            results.append({"symbol": symbol, "status": "SUCCEEDED", "freshness": fresh.to_dict()})
        except Exception as exc:
            failures += 1
            results.append({"symbol": symbol, "status": "FAILED", "reason": f"{type(exc).__name__}:{exc}"})

    return {
        "status": "SUCCEEDED" if failures == 0 else ("PARTIAL" if failures < len(results) else "FAILED"),
        "failures": failures,
        "symbols": results,
        "execution_authority": "NONE",
    }
