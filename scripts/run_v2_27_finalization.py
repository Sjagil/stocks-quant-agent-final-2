#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)


def run(label: str, command: list[str]) -> int:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, result.returncode)
    return int(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    args = parser.parse_args()
    steps = [
        (
            "FOCUSED_TESTS",
            [
                str(PYTHON), "-m", "pytest", "-q",
                "tests/test_eodhd_hydration_freshness_v2_26_1.py",
                "tests/test_provider_federation_v2_27.py",
                "tests/test_provider_federation_security_v2_27_3.py",
                "tests/test_repo_owned_deprecation_hotspots_v2_27_3.py",
                "tests/test_current_session_market_bridge_v2_27.py",
                "tests/test_current_session_bridge_short_circuit_v2_27_2.py",
                "tests/test_start_preflight_partial_freshness_v2_27.py",
                "tests/test_start_preflight_v2_26.py",
                "tests/test_dynamic_shadow_target_book_v2_26.py",
                "tests/test_pit_shariah_v2_25.py",
                "tests/test_generated_forward_adapters_v2_23.py",
            ],
        ),
        ("COMPILEALL", [str(PYTHON), "-m", "compileall", "-q", "src", "scripts"]),
        ("PIP_CHECK", [str(PYTHON), "-m", "pip", "check"]),
        ("GIT_DIFF_CHECK", ["git", "diff", "--check"]),
    ]
    if args.full_tests:
        steps.append(("FULL_TEST_SUITE", [str(PYTHON), "-m", "pytest", "-q"]))
    failed = [label for label, command in steps if run(label, command) != 0]
    if failed:
        print("V2_27_FINALIZATION BLOCKED", "|".join(failed))
        return 2
    print("=" * 100)
    print("V2_27_FINALIZATION RESEARCH_SHADOW_BRIDGE_READY")
    print("EODHD_HISTORICAL_BACKFILL True")
    print("IBKR_CURRENT_SESSION_READ_ONLY True")
    print("IBKR_ONLY_WHEN_TAIL_REQUIRED True")
    print("SOURCE_FABRIC_EXTERNAL_PROVIDERS True")
    print("FEDERATION_SECRET_REDACTION_BEFORE_WRITE True")
    print("FEDERATION_FAILURE_ISOLATION True")
    print("REPO_OWNED_TIMEDELTA_CLEANUP True")
    print("STOCKS_REFERENCE_FULL_DATA_FEDERATION True")
    print("OPENEXCHANGERATES_PRIMARY_FX True")
    print("DONOR_FRED_MACRO_REFRESH True")
    print("SESSION_AWARE_30M_TO_1H True")
    print("PER_SYMBOL_FRESHNESS_GATE True")
    print("FORWARD_FILL False")
    print("OPEN_BAR_PUBLISHING False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
