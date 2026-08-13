from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stocks.data.split_reconciliation import (
    reconcile_provider_splits,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def load_local_env() -> None:
    path = ROOT / ".env"

    if not path.is_file():
        return

    for raw in path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        os.environ.setdefault(
            key.strip(),
            value.strip()
            .strip('"')
            .strip("'"),
        )


def main() -> int:
    load_local_env()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        required=True,
    )

    parser.add_argument(
        "--ticker",
        required=True,
    )

    parser.add_argument(
        "--as-of",
        required=True,
    )

    parser.add_argument(
        "--max-median-bps",
        type=float,
        default=50.0,
    )

    parser.add_argument(
        "--max-p95-bps",
        type=float,
        default=100.0,
    )

    parser.add_argument(
        "--max-bad-fraction",
        type=float,
        default=0.01,
    )

    args = parser.parse_args()

    token = (
        os.environ.get(
            "EODHD_API_KEY"
        )
        or os.environ.get(
            "EOD_API_KEY"
        )
        or os.environ.get(
            "EODHISTORICALDATA_API_KEY"
        )
        or ""
    ).strip()

    if not token:
        raise SystemExit(
            "EODHD API token missing"
        )

    result = (
        reconcile_provider_splits(
            ROOT,
            symbol=args.symbol,
            ticker=args.ticker,
            token=token,
            as_of=args.as_of,
            max_median_bps=(
                args.max_median_bps
            ),
            max_p95_bps=(
                args.max_p95_bps
            ),
            max_bad_fraction=(
                args.max_bad_fraction
            ),
        )
    )

    artifact = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "split_reconciliation"
        / (
            args.symbol.upper()
            + ".json"
        )
    )

    artifact.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact.write_text(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
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
