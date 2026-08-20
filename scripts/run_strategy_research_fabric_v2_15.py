#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("=" * 78)
    print("RUN", " ".join(command))
    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument(
        "--max-variants-per-template",
        type=int,
    )
    parser.add_argument(
        "--with-kronos",
        action="store_true",
    )
    parser.add_argument(
        "--kronos-limit",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--kronos-stride",
        type=int,
        default=8,
    )
    args = parser.parse_args()

    indicator = [
        sys.executable,
        "scripts/run_indicator_strategy_discovery.py",
    ]
    if args.symbols:
        indicator += ["--symbols", args.symbols]
    if args.max_variants_per_template:
        indicator += [
            "--max-variants-per-template",
            str(args.max_variants_per_template),
        ]
    run(indicator)

    if args.with_kronos:
        run(
            [
                sys.executable,
                "scripts/run_kronos_strategy_research_v2_15.py",
                "--from-queue",
                "--limit",
                str(args.kronos_limit),
                "--timeframe",
                "1h",
                "--stride",
                str(args.kronos_stride),
            ]
        )

    run(
        [
            sys.executable,
            "scripts/build_research_candidate_registry.py",
        ]
    )

    print("=" * 78)
    print("STRATEGY_RESEARCH_FABRIC_V2_15 COMPLETE")
    print("INDICATOR_GENERATION True")
    print(
        "INDICATOR_PURGED_WALK_FORWARD_BACKTEST True"
    )
    print("KRONOS_RESEARCH", bool(args.with_kronos))
    print(
        "KRONOS_STANDALONE_ENTRY_AUTHORITY False"
    )
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
