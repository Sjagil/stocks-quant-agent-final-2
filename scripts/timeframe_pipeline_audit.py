from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.data.timeframe_pipeline import (
    TIMEFRAME_ORDER,
    build_timeframe_pipeline,
    materialize_context_views,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        required=True,
    )

    parser.add_argument(
        "--materialize",
        action="store_true",
    )

    args = parser.parse_args()

    symbols = [
        item.strip().upper()
        for item
        in args.symbols.split(",")
        if item.strip()
    ]

    results = []

    for symbol in symbols:
        pipeline = (
            build_timeframe_pipeline(
                ROOT,
                symbol,
            )
        )

        available = (
            pipeline
            .available_timeframes
        )

        missing = [
            timeframe
            for timeframe
            in TIMEFRAME_ORDER
            if timeframe
            not in available
        ]

        rows = {}

        for timeframe in available:
            view = pipeline.views[
                timeframe
            ]

            frame = view.frame

            rows[
                timeframe
            ] = {
                "role": (
                    view.spec.role
                ),
                "mode": (
                    view.spec.mode
                ),
                "source_timeframe": (
                    view.spec
                    .source_timeframe
                ),
                "rows": len(
                    frame
                ),
                "first": (
                    str(
                        frame.index[0]
                    )
                ),
                "last": (
                    str(
                        frame.index[-1]
                    )
                ),
            }

        status = (
            "OK"
            if not missing
            else "DEGRADED"
        )

        if "15m" not in available:
            status = (
                "BLOCKED_TACTICAL_15M"
            )

        materialized = {}

        if (
            args.materialize
            and "15m"
            in available
        ):
            materialized = (
                materialize_context_views(
                    ROOT,
                    pipeline,
                )
            )

        result = {
            "symbol": symbol,
            "status": status,
            "available": list(
                available
            ),
            "missing": missing,
            "views": rows,
            "materialized": (
                materialized
            ),
        }

        results.append(
            result
        )

        print()
        print(
            symbol,
            status,
        )

        for timeframe in (
            TIMEFRAME_ORDER
        ):
            row = rows.get(
                timeframe
            )

            if row is None:
                print(
                    timeframe,
                    "MISSING",
                )
                continue

            print(
                timeframe,
                row["role"],
                row["mode"],
                "rows=",
                row["rows"],
                "last=",
                row["last"],
            )

    output = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "timeframe_pipeline_audit.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "timeframe_pipeline_audit_v1"
                ),
                "timeframes": list(
                    TIMEFRAME_ORDER
                ),
                "results": results,
                "execution_authority": (
                    "NONE"
                ),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "ARTIFACT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
