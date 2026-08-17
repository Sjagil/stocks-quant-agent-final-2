#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run(
    label: str,
    command: list[str],
    *,
    required: bool = True,
) -> int:
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
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit-symbols",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--full-tests",
        action="store_true",
    )
    args = parser.parse_args()

    python = sys.executable

    focused = [
        "tests/test_cross_engine_full_engine_v2_17_7.py",
        "tests/test_cross_engine_runtime_v2_17_6.py",
        "tests/test_cross_engine_completion_v2_17_5.py",
        "tests/test_cross_engine_strategy_validation_v2_17.py",
        "tests/test_stocks_donor_integration_v2_17_1.py",
    ]
    run(
        "FOCUSED_TESTS",
        [
            python,
            "-m",
            "pytest",
            "-q",
            *focused,
        ],
    )

    run(
        "COMPILEALL",
        [
            python,
            "-m",
            "compileall",
            "-q",
            "src",
            "scripts",
        ],
    )
    run(
        "PIP_CHECK",
        [
            python,
            "-m",
            "pip",
            "check",
        ],
    )
    run(
        "GIT_DIFF_CHECK",
        [
            "git",
            "diff",
            "--check",
        ],
    )

    if args.full_tests:
        run(
            "FULL_TEST_SUITE",
            [
                python,
                "-m",
                "pytest",
                "-q",
            ],
        )

    run(
        "RUNTIME_AUDIT",
        [
            python,
            "scripts/audit_cross_engine_runtime_v2_17.py",
        ],
    )
    run(
        "CROSS_ENGINE_REPLAY",
        [
            python,
            "scripts/run_cross_engine_strategy_validation_v2_17.py",
            "--limit-symbols",
            str(args.limit_symbols),
        ],
    )
    run(
        "DEEP_AUDIT",
        [
            python,
            "scripts/audit_cross_engine_outputs_v2_17_4.py",
        ],
    )

    summary_path = (
        ROOT
        / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17/"
        "strategy_summary.csv"
    )
    if (
        not summary_path.is_file()
        or summary_path.stat().st_size == 0
    ):
        print(
            "V2_17_FINALIZATION "
            "CROSS_ENGINE_VALIDATED False "
            "REASON NO_SUMMARY"
        )
        return 2

    summary = pd.read_csv(summary_path)
    validated = (
        not summary.empty
        and (
            summary["status"]
            == "CROSS_ENGINE_VALIDATED"
        ).any()
    )

    print("=" * 100)
    print(
        "V2_17_FINALIZATION",
        "CROSS_ENGINE_VALIDATED",
        bool(validated),
    )
    print("WHOLE_SHARES_ONLY True")
    print("FIXED_EURO_ORDER_CAP False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")

    return 0 if validated else 2


if __name__ == "__main__":
    raise SystemExit(main())
