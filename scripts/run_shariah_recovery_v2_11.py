#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(label: str, args: list[str], *, required: bool = True) -> int:
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
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    current = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification"
    )
    baseline = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification_v2_10_baseline"
    )

    if current.is_dir() and not baseline.exists():
        shutil.copytree(current, baseline)
        print("BASELINE_SAVED", baseline)

    run(
        "SHARIAH_FINANCIAL_VERIFICATION",
        [
            "scripts/run_shariah_financial_verification.py",
            "--as-of",
            args.as_of,
            "--limit",
            str(args.limit),
        ],
    )

    run(
        "SEC_MAPPING_AUDIT",
        ["scripts/audit_sec_mapping_recovery_v2_11.py"],
        required=False,
    )

    run(
        "ATTESTATION_QUEUE",
        [
            "scripts/build_shariah_attestation_queue_v2_10.py",
            "--as-of",
            args.as_of,
        ],
    )

    run(
        "SEC_UNIT_GAPS",
        [
            "scripts/profile_sec_unit_gaps_v2_11.py",
            "--as-of",
            args.as_of,
        ],
        required=False,
    )

    print("=" * 78)
    print("SHARIAH_RECOVERY_V2_11 COMPLETE")
    print("AUTOMATIC_ATTESTATION", False)
    print("AUTOMATIC_ZERO_IMPUTATION", False)
    print("AUTOMATIC_FX_CONVERSION", False)
    print("EXECUTION_AUTHORITY", "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
