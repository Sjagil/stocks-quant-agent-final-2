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
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--kronos-limit", type=int, default=1)
    parser.add_argument("--kronos-stride", type=int, default=32)
    parser.add_argument("--skip-hydration", action="store_true")
    parser.add_argument("--skip-kronos", action="store_true")
    args = parser.parse_args()

    if not args.skip_hydration:
        run(
            [
                sys.executable,
                "scripts/hydrate_active_swing_queue_v2_15_3.py",
                "--from-queue",
                "--limit",
                str(args.limit),
                "--as-of",
                args.as_of,
            ]
        )

    run(
        [
            sys.executable,
            "scripts/run_multitimeframe_strategy_research_v2_15_1.py",
            "--from-queue",
            "--limit",
            str(args.limit),
        ]
    )

    if not args.skip_kronos:
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
                "--sample-count",
                "1",
            ]
        )

    run(
        [
            sys.executable,
            "scripts/build_research_candidate_registry.py",
        ]
    )

    # This is still shadow/research orchestration. It proves the complete
    # research-to-decision path without sending or authorizing broker orders.
    if (ROOT / "scripts/run_agent_fabric_v2_14.py").is_file():
        run(
            [
                sys.executable,
                "scripts/run_agent_fabric_v2_14.py",
                "--timeframe",
                "1h",
            ]
        )

    print("=" * 78)
    print("PRACTICE_RESEARCH_V2_15_3 COMPLETE")
    print("TIMEFRAME_CHAIN 1W->1D->4H/2H->1H->15M")
    print("STRATEGY_GENERATION True")
    print("PURGED_WALK_FORWARD True")
    print("KRONOS_RESEARCH", not args.skip_kronos)
    print("BROKER_ORDER_SUBMISSION False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
