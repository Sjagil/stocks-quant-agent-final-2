from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.data.reference_15m_intake import (
    build_reference_15m,
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

    args = parser.parse_args()

    results = []

    for raw_symbol in args.symbols:
        symbol = (
            raw_symbol
            .strip()
            .upper()
        )

        result = build_reference_15m(
            ROOT,
            args.index,
            symbol,
            as_of=args.as_of,
            min_provider_coverage=(
                args.min_provider_coverage
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
            result[
                "rows"
            ],
        )
        print(
            "LAST",
            result[
                "last"
            ],
        )
        print(
            "APPENDED_EODHD",
            result[
                "appended_eodhd_rows"
            ],
        )
        print(
            "APPENDED_YFINANCE",
            result[
                "appended_yfinance_rows"
            ],
        )
        print(
            "EODHD_COVERAGE",
            result[
                "eodhd_coverage"
            ],
        )
        print(
            "YFINANCE_COVERAGE",
            result[
                "yfinance_coverage"
            ],
        )

    artifact = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "reference_15m_intake.json"
    )

    artifact.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact.write_text(
        json.dumps(
            {
                "schema": (
                    "reference_15m_intake_v1"
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
        artifact,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
