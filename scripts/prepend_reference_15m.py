from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.data.reference_15m_intake import (
    prepend_reference_15m,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--index",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--provider",
        default="EODHD",
    )

    parser.add_argument(
        "--as-of",
        required=True,
    )

    parser.add_argument(
        "--min-provider-coverage",
        type=float,
        default=0.95,
    )

    parser.add_argument(
        "--max-overlap-median-bps",
        type=float,
        default=50.0,
    )

    parser.add_argument(
        "--max-overlap-p95-bps",
        type=float,
        default=100.0,
    )

    parser.add_argument(
        "--max-overlap-bad-fraction",
        type=float,
        default=0.01,
    )

    args = parser.parse_args()

    results = []

    for raw_symbol in args.symbols:
        symbol = (
            raw_symbol.strip()
            .upper()
        )

        result = prepend_reference_15m(
            ROOT,
            args.index,
            symbol,
            provider=args.provider,
            as_of=args.as_of,
            min_provider_coverage=(
                args.min_provider_coverage
            ),
            max_overlap_median_bps=(
                args.max_overlap_median_bps
            ),
            max_overlap_p95_bps=(
                args.max_overlap_p95_bps
            ),
            max_overlap_bad_fraction=(
                args.max_overlap_bad_fraction
            ),
        )

        results.append(
            result
        )

        print()
        print(
            symbol
        )
        print(
            "ROWS",
            result["rows"],
        )
        print(
            "FIRST",
            result["first"],
        )
        print(
            "LAST",
            result["last"],
        )
        print(
            "PREPENDED",
            result[
                "prepended_rows"
            ],
        )
        print(
            "COVERAGE",
            result[
                "incoming_coverage"
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
        / "reference_15m_prepend.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "reference_15m_"
                    "historical_prepend_v1"
                ),
                "results": results,
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
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
    raise SystemExit(
        main()
    )
