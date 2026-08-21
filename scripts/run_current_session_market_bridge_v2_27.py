#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from stocks.data.current_session_bridge_v2_27 import bridge_symbol_v227, write_bridge_audit_v227
from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/current_session_market_bridge_v2_27"


def _symbols(path: Path, limit: int) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if "symbol" not in frame:
        raise ValueError("symbol column missing")
    result: list[str] = []
    for value in frame["symbol"]:
        symbol = str(value).strip().upper()
        if symbol and symbol not in result:
            result.append(symbol)
        if len(result) >= limit:
            break
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols-from",
        default=str(ROOT / "artifacts/research_runtime/contextual_1h_hydration/usable_candidates.csv"),
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--decision-time", default=None)
    parser.add_argument("--integration", default="stocks_ibkr_reference")
    args = parser.parse_args()

    decision_time = pd.Timestamp(args.decision_time) if args.decision_time else pd.Timestamp(datetime.now(UTC))
    decision_time = (
        decision_time.tz_localize("UTC")
        if decision_time.tzinfo is None
        else decision_time.tz_convert("UTC")
    )
    symbols = _symbols(Path(args.symbols_from), int(args.limit))
    if not symbols:
        print("CURRENT_SESSION_MARKET_BRIDGE_V2_27 BLOCKED ZERO_SYMBOLS")
        return 2

    registry = IntegrationRegistry.load(ROOT / "config/integrations.yaml", project_root=ROOT)
    runner = IntegrationRunner(registry)
    response = runner.run(
        args.integration,
        "historical_bars_read_only",
        {
            "symbols": symbols,
            "duration": "5 D",
            "bar_size": "30 mins",
            "what_to_show": "TRADES",
            "use_rth": True,
            "keep_up_to_date": False,
        },
        timeout_seconds=180,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "integration_response.json").write_text(
        json.dumps(response.to_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    if not response.ok or not response.artifacts:
        print("CURRENT_SESSION_MARKET_BRIDGE_V2_27 BLOCKED INTEGRATION_FAILED", response.error)
        print("BROKER_CALLS 0")
        print("ORDER_CALLS 0")
        print("EXECUTION_AUTHORITY NONE")
        return 2

    payload = json.loads(Path(response.artifacts[0].path).read_text(encoding="utf-8"))
    if int(payload.get("broker_write_calls", 0)) != 0:
        raise RuntimeError("BROKER_WRITE_COUNTER_NONZERO_BLOCKED")

    by_symbol = payload.get("records") or {}
    provider_results = payload.get("symbol_results") or {}
    rows: list[dict] = []
    for symbol in symbols:
        provider = (provider_results.get(symbol) if isinstance(provider_results, dict) else None) or {}
        records = (by_symbol.get(symbol) if isinstance(by_symbol, dict) else None) or []
        if str(provider.get("status")) != "OK":
            rows.append(
                {
                    "symbol": symbol,
                    "status": "BLOCKED",
                    "blockers": ["IBKR_HISTORICAL_READ_FAILED"],
                    "provider": provider,
                    "execution_authority": "NONE",
                    "broker_write_calls": 0,
                    "order_calls": 0,
                }
            )
            continue
        try:
            rows.append(
                bridge_symbol_v227(ROOT, symbol, records, decision_time=decision_time)
            )
        except Exception as exc:
            rows.append(
                {
                    "symbol": symbol,
                    "status": "BLOCKED",
                    "blockers": [f"{type(exc).__name__}:{exc}"],
                    "execution_authority": "NONE",
                    "broker_write_calls": 0,
                    "order_calls": 0,
                }
            )

    fresh = [row for row in rows if bool(row.get("operationally_fresh"))]
    blocked = [row for row in rows if not bool(row.get("operationally_fresh"))]
    audit = {
        "schema": "current_session_market_bridge_v2_27",
        "decision_time": decision_time.isoformat(),
        "symbols": symbols,
        "symbol_count": len(symbols),
        "fresh_count": len(fresh),
        "blocked_count": len(blocked),
        "all_fresh": len(fresh) == len(symbols),
        "market_data_read_calls": int(payload.get("historical_data_calls", 0)),
        "broker_write_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
        "results": rows,
    }
    write_bridge_audit_v227(OUTPUT / "audit.json", audit)

    print(
        "CURRENT_SESSION_MARKET_BRIDGE_V2_27",
        "SYMBOLS", len(symbols),
        "FRESH", len(fresh),
        "BLOCKED", len(blocked),
        "ALL_FRESH", audit["all_fresh"],
    )
    for row in rows:
        print(
            "BRIDGE", row["symbol"], row["status"],
            "LATEST", row.get("latest_after_bridge", row.get("historical_last")),
            "BLOCKERS", "|".join(row.get("blockers") or []),
        )
    print("MARKET_DATA_READ_CALLS", audit["market_data_read_calls"])
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", OUTPUT)
    return 0 if audit["all_fresh"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
