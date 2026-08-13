from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.data.session_hourly import (
    synchronize_hourly,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--as-of",
        required=True,
    )

    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.95,
    )

    parser.add_argument(
        "--max-overlap-median-bps",
        type=float,
        default=50.0,
    )

    args = parser.parse_args()

    results = []

    for raw_symbol in args.symbols:
        symbol = (
            raw_symbol
            .strip()
            .upper()
        )

        result = synchronize_hourly(
            ROOT,
            symbol,
            as_of=args.as_of,
            min_coverage=(
                args.min_coverage
            ),
            max_overlap_median_bps=(
                args.max_overlap_median_bps
            ),
        )

        results.append(
            result
        )

        print()
        print(symbol)
        print(
            "ROWS",
            result["rows"],
        )
        print(
            "LAST_BAR",
            result[
                "last_bar"
            ],
        )
        print(
            "SWITCH",
            result[
                "switch_time"
            ],
        )
        print(
            "TAIL_ROWS",
            result[
                "derived_tail_rows"
            ],
        )
        print(
            "COVERAGE",
            result[
                "coverage"
            ],
        )
        print(
            "OVERLAP",
            result[
                "overlap"
            ],
        )

    output = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "session_hourly_sync.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "session_hourly_sync_v1"
                ),
                "results": results,
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            },
            indent=2,
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
    raise SystemExit(
        main()
    )
