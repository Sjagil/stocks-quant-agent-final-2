#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str]) -> None:
    print("=" * 100, flush=True)
    print("RUN", label, flush=True)
    print("COMMAND", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode, flush=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize the v2.21 RL/MARL pipeline.")
    parser.add_argument("--config", type=Path, default=ROOT / "config/rl_marl_pipeline_v2_21.yaml")
    parser.add_argument("--full", action="store_true", help="Run the 10-seed matrix instead of smoke mode")
    parser.add_argument("--full-tests", action="store_true")
    parser.add_argument("--max-folds", type=int)
    args = parser.parse_args()
    python = sys.executable
    focused = [
        "tests/test_rl_marl_pipeline_v2_21.py",
        "tests/test_rl_marl_v2_21.py",
        "tests/test_rl_rewards.py",
        "tests/test_rl_walk_forward_v2.py",
        "tests/test_rl_promotion.py",
        "tests/test_trade_intent.py",
    ]
    run("FOCUSED_TESTS", [python, "-m", "pytest", "-q", *focused])
    run("COMPILEALL", [python, "-m", "compileall", "-q", "src", "scripts"])
    run("PIP_CHECK", [python, "-m", "pip", "check"])
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"])
    if args.full_tests:
        run("FULL_TEST_SUITE", [python, "-m", "pytest", "-q"])
    command = [
        python,
        "scripts/run_rl_marl_pipeline_v2_21.py",
        "--config",
        str(args.config),
    ]
    if not args.full:
        command.append("--smoke")
    else:
        command.append("--verify-reproducibility")
    if args.max_folds is not None:
        command.extend(["--max-folds", str(args.max_folds)])
    run("RL_MARL_PIPELINE", command)
    print("=" * 100)
    print("V2_21_FINALIZATION PIPELINE_READY True")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
