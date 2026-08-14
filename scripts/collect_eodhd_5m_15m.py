from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.data.eodhd_5m_source import (
    collect_eodhd_5m_15m,
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
        "--start",
        required=True,
    )

    parser.add_argument(
        "--end",
        required=True,
    )

    parser.add_argument(
        "--as-of",
        required=True,
    )

    parser.add_argument(
        "--chunk-days",
        type=int,
        default=590,
    )

    args = parser.parse_args()

    result = collect_eodhd_5m_15m(
        ROOT,
        symbols=args.symbols,
        start=args.start,
        end=args.end,
        as_of=args.as_of,
        chunk_days=args.chunk_days,
    )

    print(
        json.dumps(
            {
                "schema": (
                    result["schema"]
                ),
                "run_id": (
                    result["run_id"]
                ),
                "provider_calls": (
                    result[
                        "provider_calls"
                    ]
                ),
                "symbols": [
                    {
                        "symbol": (
                            row["symbol"]
                        ),
                        "rows": (
                            row["rows"]
                        ),
                        "first": (
                            row[
                                "first_timestamp"
                            ]
                        ),
                        "last": (
                            row[
                                "last_timestamp"
                            ]
                        ),
                        "source_interval": (
                            row[
                                "source_interval"
                            ]
                        ),
                    }
                    for row
                    in result["bars"]
                ],
                "index_path": (
                    result[
                        "index_path"
                    ]
                ),
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
