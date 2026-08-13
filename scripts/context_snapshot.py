from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stocks.research.context_snapshot import (
    collect_context_snapshot,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def load_env(
    path: Path,
) -> None:
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
            value
            .strip()
            .strip('"')
            .strip("'"),
        )


def main() -> int:
    load_env(
        ROOT / ".env"
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default=(
            "AAPL,AMD,MSFT,NVDA,"
            "SPY,QQQ,GLD,SLV,CPER"
        ),
    )

    parser.add_argument(
        "--no-news",
        action="store_true",
    )

    parser.add_argument(
        "--no-macro",
        action="store_true",
    )

    parser.add_argument(
        "--no-gex",
        action="store_true",
    )

    args = parser.parse_args()

    symbols = tuple(
        value.strip().upper()
        for value in args.symbols.split(",")
        if value.strip()
    )

    result = collect_context_snapshot(
        ROOT,
        symbols,
        news=not args.no_news,
        macro=not args.no_macro,
        gex=not args.no_gex,
    )

    print(
        json.dumps(
            {
                "artifact": (
                    result[
                        "artifact"
                    ]
                ),
                "symbols": (
                    result[
                        "symbols"
                    ]
                ),
                "news_status": (
                    result
                    .get(
                        "news",
                        {},
                    )
                    .get(
                        "status"
                    )
                ),
                "macro_status": (
                    result
                    .get(
                        "macro",
                        {},
                    )
                    .get(
                        "status"
                    )
                ),
                "gex_status": (
                    result
                    .get(
                        "gex",
                        {},
                    )
                    .get(
                        "status"
                    )
                ),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
