#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def focused_tests() -> list[str]:
    return [
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "tests").glob("test_*v2_19*.py"))
    ]


def run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    parser.add_argument("--refresh-v2-18", action="store_true")
    parser.add_argument("--limit-symbols", type=int, default=5)
    parser.add_argument("--skip-forward-signals", action="store_true")
    args = parser.parse_args()

    tests = focused_tests()
    if not tests:
        raise SystemExit("no v2.19 tests discovered")
    python = sys.executable
    run("FOCUSED_TESTS", [python, "-m", "pytest", "-q", *tests])
    run("COMPILEALL", [python, "-m", "compileall", "-q", "src", "scripts"])
    run("PIP_CHECK", [python, "-m", "pip", "check"])
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"])
    if args.full_tests:
        run("FULL_TEST_SUITE", [python, "-m", "pytest", "-q"])

    automation = [python, "scripts/run_validated_strategy_automation_v2_19.py"]
    if args.refresh_v2_18:
        automation.extend(
            ["--refresh-v2-18", "--limit-symbols", str(args.limit_symbols)]
        )
    if args.skip_forward_signals:
        automation.append("--skip-forward-signals")
    run("VALIDATED_STRATEGY_AUTOMATION", automation)

    print("=" * 100)
    print("V2_19_FINALIZATION AUTOMATION_READY True")
    print("STRICT_VALIDATED_DEPLOYMENT_GATE True")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
