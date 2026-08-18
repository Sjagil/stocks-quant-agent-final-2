#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(
    label: str,
    args: list[str],
    *,
    required: bool = True,
) -> int:
    print("=" * 78)
    print("RUN", label)
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
    )
    print("RESULT", label, completed.returncode)
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--queue-limit", type=int, default=12)
    args = parser.parse_args()

    run(
        "AGENT_STACK",
        ["scripts/check_agent_stack_v2_12.py"],
    )
    run(
        "TRAINING_QUEUE",
        [
            "scripts/build_agent_training_queue_v2_13.py",
            "--timeframe",
            args.timeframe,
            "--limit",
            str(args.queue_limit),
        ],
    )
    run(
        "AGENT_SHADOW_FUSION",
        [
            "scripts/run_agent_fabric_v2_13.py",
            "--timeframe",
            args.timeframe,
        ],
    )

    print("=" * 78)
    print("AGENT_PIPELINE_V2_13 COMPLETE")
    print("VALIDATION_AND_DEPLOYMENT ARE EXPLICIT STEPS")
    print("LIVE_AUTHORITY NONE")
    print("BROKER_ORDER_SUBMISSION DISABLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
