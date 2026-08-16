#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from stocks.agents.candle_fabric import candle_summary, frame_for_timeframe
from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="AAPL,AMD,MSFT,NVDA,SPY")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--sample-rows", type=int, default=512)
    args = parser.parse_args()

    symbols = [
        item.strip().upper()
        for item in args.symbols.split(",")
        if item.strip()
    ]

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    rows = []
    for symbol in symbols:
        try:
            frame = frame_for_timeframe(ROOT, symbol, args.timeframe)
            summary = candle_summary(frame)
            local_ok = True
            local_error = None
        except Exception as exc:
            frame = None
            summary = {}
            local_ok = False
            local_error = f"{type(exc).__name__}:{exc}"

        nautilus_ok = False
        nautilus_error = None
        nautilus_data = {}

        if frame is not None:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"{symbol}_{args.timeframe}.parquet"
                frame.tail(max(1, int(args.sample_rows))).to_parquet(path)
                response = runner.run(
                    "nautilus",
                    "candle_validate",
                    {
                        "input_parquet": str(path),
                        "symbol": symbol,
                        "timeframe": args.timeframe,
                        "sample_rows": int(args.sample_rows),
                    },
                    timeout_seconds=120,
                )
                nautilus_ok = response.ok
                nautilus_error = response.error
                nautilus_data = dict(response.data or {})

        rows.append(
            {
                "symbol": symbol,
                "timeframe": args.timeframe,
                "canonical_ok": local_ok,
                "canonical_error": local_error,
                "canonical_summary": summary,
                "nautilus_ok": nautilus_ok,
                "nautilus_error": nautilus_error,
                "nautilus_summary": nautilus_data,
                "execution_authority": "NONE",
            }
        )

        print(
            "CANDLE",
            symbol,
            args.timeframe,
            "CANONICAL",
            local_ok,
            "NAUTILUS",
            nautilus_ok,
            "ROWS",
            summary.get("rows"),
            "ERROR",
            local_error or nautilus_error,
        )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "candle_fabric_v2_12"
    )
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "candle_fabric_v2_12",
        "rows": rows,
        "all_canonical_ok": all(row["canonical_ok"] for row in rows),
        "all_nautilus_ok": all(row["nautilus_ok"] for row in rows),
        "execution_authority": "NONE",
    }
    (output / "audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print("CANDLE_FABRIC_V2_12 COMPLETE")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
