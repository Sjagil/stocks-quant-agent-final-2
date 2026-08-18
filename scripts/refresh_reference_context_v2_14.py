#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of")
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument(
        "--symbols",
        default="AAPL,AMD,MSFT,NVDA,SPY,QQQ,GLD,SLV,SMCI,WDC,OMER,ETON,NU",
    )
    parser.add_argument("--skip-market-context", action="store_true")
    args = parser.parse_args()

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    discovery_payload = {
        "limit": int(args.limit),
        "minimum_total_score": 45.0,
    }
    if args.as_of:
        discovery_payload["as_of"] = args.as_of

    discovery = runner.run(
        "stocks_context_reference",
        "discovery_context",
        discovery_payload,
        timeout_seconds=900,
    )
    print(
        "REFERENCE_DISCOVERY_CONTEXT",
        discovery.state.value,
        "OK",
        discovery.ok,
        "ERROR",
        discovery.error,
    )

    if not args.skip_market_context:
        market = runner.run(
            "stocks_context_reference",
            "market_context",
            {
                "symbols": [
                    item.strip().upper()
                    for item in args.symbols.split(",")
                    if item.strip()
                ],
                "fetch_options": True,
                "max_expirations": 4,
            },
            timeout_seconds=900,
        )
        print(
            "REFERENCE_MARKET_CONTEXT",
            market.state.value,
            "OK",
            market.ok,
            "ERROR",
            market.error,
        )

    print("EXECUTION_AUTHORITY NONE")
    print("BROKER_ORDER_SUBMISSION False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
