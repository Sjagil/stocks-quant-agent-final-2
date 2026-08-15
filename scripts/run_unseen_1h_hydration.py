#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.research.eodhd_holdout_hydration import (
    existing_hourly_state,
    hydrate_symbol,
    load_holdout_config,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/unseen_1h_hydration"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--max-symbols", type=int, default=24)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_holdout_config(ROOT)
    symbols = list(config["symbols"])
    minimum_rows = int(config["minimum_rows"])
    minimum_coverage = float(config["minimum_coverage"])
    start = str(config["start"])
    OUTPUT.mkdir(parents=True, exist_ok=True)

    queue_rows = []
    for symbol in symbols:
        state = existing_hourly_state(
            ROOT, symbol, minimum_rows=minimum_rows, as_of=args.as_of
        )
        queue_rows.append({
            "symbol": symbol,
            "existing_usable": bool(state["usable"]),
            "existing_rows": int(state.get("rows") or 0),
            "existing_path": state.get("path"),
            "queue_reason": state.get("reason"),
            "holdout_frozen": True,
            "execution_authority": "NONE",
        })
    queue = pd.DataFrame(queue_rows)
    queue.to_csv(OUTPUT / "hydration_queue.csv", index=False)
    missing = queue.loc[~queue["existing_usable"]].head(max(int(args.max_symbols), 0))

    print(
        "UNSEEN_1H_HYDRATION_QUEUE",
        "HOLDOUT", len(symbols),
        "EXISTING_USABLE", int(queue["existing_usable"].sum()),
        "TO_HYDRATE", len(missing),
    )
    if not missing.empty:
        print(missing[["symbol", "existing_rows", "queue_reason"]].to_string(index=False))
    if args.dry_run:
        return 0

    load_project_env(ROOT)
    api_key = secret("EODHD_API_KEY", "EOD_API_KEY", "EODHISTORICALDATA_API_KEY")
    if not api_key:
        print("EODHD_KEY_MISSING; hydration skipped fail-closed")
        return 0

    results = []
    http = ProviderHTTPClient(
        user_agent="stocks-quant-agent/eodhd-1h-holdout-hydration"
    )
    try:
        for symbol in missing["symbol"].astype(str):
            try:
                result = hydrate_symbol(
                    ROOT,
                    symbol,
                    start=start,
                    as_of=args.as_of,
                    api_key=api_key,
                    minimum_rows=minimum_rows,
                    minimum_coverage=minimum_coverage,
                    client=http,
                )
                record = result.to_dict()
                print(
                    "HYDRATE", symbol, record["status"],
                    "ROWS", record["rows"],
                    "COVERAGE", record["coverage"],
                    "SPLITS", record["split_count"],
                )
            except Exception as exc:
                record = {
                    "symbol": symbol,
                    "status": "FAILED",
                    "rows": 0,
                    "first": None,
                    "last": None,
                    "split_count": 0,
                    "coverage": 0.0,
                    "provider_requests": 0,
                    "output": None,
                    "reason": f"{type(exc).__name__}: {exc}",
                    "execution_authority": "NONE",
                    "broker_calls": 0,
                    "order_calls": 0,
                }
                print("HYDRATE", symbol, "FAILED", record["reason"])
            results.append(record)
    finally:
        http.close()

    result_frame = pd.DataFrame(results)
    result_frame.to_csv(OUTPUT / "hydration_results.csv", index=False)

    post_rows = []
    for symbol in symbols:
        state = existing_hourly_state(
            ROOT, symbol, minimum_rows=minimum_rows, as_of=args.as_of
        )
        post_rows.append({
            "symbol": symbol,
            "usable": bool(state["usable"]),
            "rows": int(state.get("rows") or 0),
            "path": state.get("path"),
            "reason": state.get("reason"),
        })
    post = pd.DataFrame(post_rows)
    post.to_csv(OUTPUT / "holdout_state.csv", index=False)

    audit = {
        "schema": "unseen_1h_hydration_v2_4",
        "holdout_symbols": len(symbols),
        "usable_after_run": int(post["usable"].sum()),
        "attempted": int(len(missing)),
        "hydrated": int(
            (result_frame.get("status", pd.Series(dtype=str)) == "HYDRATED").sum()
        ) if not result_frame.empty else 0,
        "failed": int(
            (result_frame.get("status", pd.Series(dtype=str)) == "FAILED").sum()
        ) if not result_frame.empty else 0,
        "selection_uses_strategy_outcomes": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "UNSEEN_1H_HYDRATION",
        "USABLE", audit["usable_after_run"],
        "HYDRATED", audit["hydrated"],
        "FAILED", audit["failed"],
    )
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
