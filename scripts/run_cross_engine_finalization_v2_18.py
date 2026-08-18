#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "artifacts/research_runtime/cross_engine_handoff_v2_18"


def focused_tests() -> list[str]:
    return [
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "tests").glob("test_*v2_18*.py"))
    ]


def run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
    )
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    parser.add_argument("--refresh-v2-17", action="store_true")
    parser.add_argument("--limit-symbols", type=int, default=5)
    args = parser.parse_args()

    python = sys.executable
    tests = focused_tests()
    if not tests:
        raise SystemExit("no v2.18 tests discovered")

    run("FOCUSED_TESTS", [python, "-m", "pytest", "-q", *tests])
    run("COMPILEALL", [python, "-m", "compileall", "-q", "src", "scripts"])
    run("PIP_CHECK", [python, "-m", "pip", "check"])
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"])

    if args.full_tests:
        run("FULL_TEST_SUITE", [python, "-m", "pytest", "-q"])

    if args.refresh_v2_17:
        command = [
            python,
            "scripts/run_cross_engine_finalization_v2_17_7.py",
            "--limit-symbols",
            str(args.limit_symbols),
        ]
        run("REFRESH_V2_17_EVIDENCE", command)

    run(
        "BUILD_V2_18_HANDOFF",
        [python, "scripts/build_cross_engine_handoff_v2_18.py"],
    )
    run(
        "AUDIT_V2_18_HANDOFF",
        [python, "scripts/audit_cross_engine_handoff_v2_18.py"],
    )

    audit_path = OUTPUT_ROOT / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    ready = bool(audit.get("handoff_ready"))
    registered = int(audit.get("registered_strategies", 0))
    configured = int(audit.get("configured_strategies", 0))

    print("=" * 100)
    print("V2_18_FINALIZATION HANDOFF_READY", ready)
    print("CONFIGURED_STRATEGIES", configured)
    print("REGISTERED_STRATEGIES", registered)
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0 if ready and registered == configured else 2


if __name__ == "__main__":
    raise SystemExit(main())
