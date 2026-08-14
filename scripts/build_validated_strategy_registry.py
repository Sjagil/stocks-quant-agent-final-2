#!/usr/bin/env python3

from pathlib import Path

from stocks.research.validated_strategy_registry import (
    write_validated_strategy_registry,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def main() -> int:
    frame, audit, path = (
        write_validated_strategy_registry(
            ROOT
        )
    )

    print(
        frame.to_string(
            index=False
        )
    )

    print()

    print(
        "FINALIST_CANDIDATES",
        audit[
            "finalist_candidate_count"
        ],
    )

    print(
        "CHALLENGERS",
        audit[
            "challenger_count"
        ],
    )

    print(
        "OUTPUT",
        path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
