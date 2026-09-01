#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.screener_v2_44 import run_production_screener_v244


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed production candidate screener v2.44"
    )
    parser.add_argument(
        "--offline-input", help="JSON fixture with a data list; never calls EODHD"
    )
    parser.add_argument(
        "--now", help="UTC timestamp override for deterministic replay/self-check"
    )
    args = parser.parse_args()

    offline_rows = None
    if args.offline_input:
        payload = json.loads(Path(args.offline_input).read_text(encoding="utf-8"))
        offline_rows = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(offline_rows, list):
            raise ValueError(
                "offline input must be a list or an object containing data"
            )

    frame, result, output = run_production_screener_v244(
        ROOT,
        offline_rows=offline_rows,
        now=args.now,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if not frame.empty:
        columns = [
            "rank",
            "symbol",
            "lane",
            "classification",
            "total_score",
            "return_1d_pct",
            "return_5d_pct",
            "screen_eligible",
            "shariah_status",
            "trade_eligible",
            "blockers",
        ]
        print(
            frame[[column for column in columns if column in frame]]
            .head(50)
            .to_string(index=False)
        )
    print("OUTPUT", output)
    print("EXECUTION_AUTHORITY NONE")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    return 0 if result.status == "SUCCEEDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
