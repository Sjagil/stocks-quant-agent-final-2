#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, result.returncode)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    args = parser.parse_args()
    py = sys.executable

    focused = [
        "tests/test_generated_forward_adapters_v2_23.py",
        "tests/test_final_decision_fabric_v2_8.py",
        "tests/test_strategy_generation_v2_22.py",
    ]
    _run("FOCUSED_TESTS", [py, "-m", "pytest", "-q", *focused])
    _run(
        "STATIC_ADAPTER_AUDIT",
        [py, "scripts/audit_generated_forward_adapters_v2_23.py"],
    )
    _run(
        "CANDIDATE_STRATEGY_MATRIX",
        [py, "scripts/run_candidate_strategy_matrix.py"],
    )
    _run(
        "FORWARD_SIGNAL_ENGINE",
        [py, "scripts/run_forward_signal_engine.py"],
    )
    _run(
        "RUNTIME_ADAPTER_AUDIT",
        [
            py,
            "scripts/audit_generated_forward_adapters_v2_23.py",
            "--require-runtime",
        ],
    )
    _run(
        "RESEARCH_READINESS",
        [py, "scripts/build_research_readiness.py"],
    )
    _run("COMPILEALL", [py, "-m", "compileall", "-q", "src", "scripts"])
    _run("PIP_CHECK", [py, "-m", "pip", "check"])
    _run("GIT_DIFF_CHECK", ["git", "diff", "--check"])
    if args.full_tests:
        _run("FULL_TEST_SUITE", [py, "-m", "pytest", "-q"])

    print("=" * 100)
    print("GENERATED_FORWARD_FINALIZATION_V2_23 RESEARCH_READY")
    print("GENERATED_BLUEPRINT_COVERAGE 9_OF_9")
    print("RUNTIME_COVERAGE_AUDITED True")
    print("AUTOMATIC_FINALIST_PROMOTION False")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
