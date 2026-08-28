#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(label: str, command: list[str]) -> int:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode)
    return completed.returncode


def static_contract() -> None:
    config = json.loads((ROOT / "config/pit_shariah_portfolio_v2_25_26.json").read_text(encoding="utf-8"))
    if config.get("execution_authority") != "NONE":
        raise ValueError("config grants execution authority")
    if config["shariah"].get("automatic_attestation") is not False:
        raise ValueError("automatic Shariah attestation must stay disabled")
    if config["portfolio"].get("broker_submission_enabled") is not False:
        raise ValueError("broker submission must stay disabled")
    if config["portfolio"].get("automatic_live_promotion") is not False:
        raise ValueError("automatic live promotion must stay disabled")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    args = parser.parse_args()
    static_contract()
    jobs = [
        (
            "FOCUSED_TESTS",
            [
                PYTHON, "-m", "pytest", "-q",
                "tests/test_pit_shariah_v2_25.py",
                "tests/test_dynamic_shadow_target_book_v2_26.py",
                "tests/test_start_preflight_v2_26.py",
                "tests/test_pit_shariah_rl_v2_25.py",
                "tests/test_dynamic_validated_deployment_v2_24.py",
                "tests/test_pit_training_v2_24.py",
                "tests/test_generated_forward_adapters_v2_23.py",
            ],
        ),
        ("DYNAMIC_VALIDATED_DEPLOYMENT", [PYTHON, "scripts/run_dynamic_validated_deployment_v2_24.py"]),
        ("DYNAMIC_FORWARD_SIGNAL_ENGINE", [PYTHON, "scripts/run_dynamic_forward_signal_engine_v2_24.py"]),
        ("RESEARCH_READINESS", [PYTHON, "scripts/build_research_readiness.py"]),
        ("COMPILEALL", [PYTHON, "-m", "compileall", "-q", "src", "scripts"]),
        ("PIP_CHECK", [PYTHON, "-m", "pip", "check"]),
        ("GIT_DIFF_CHECK", ["git", "diff", "--check"]),
    ]
    if args.full_tests:
        jobs.append(("FULL_TEST_SUITE", [PYTHON, "-m", "pytest", "-q"]))
    failed = False
    for label, command in jobs:
        if run(label, command) != 0:
            failed = True
            break
    print("=" * 100)
    if failed:
        print("V2_25_26_FINALIZATION BLOCKED")
        return 2
    print("V2_25_26_FINALIZATION RESEARCH_SHADOW_READY")
    print("PIT_SHARIAH_CURRENT_ENTRYPOINT_READY", True)
    print("PIT_SHARIAH_HISTORICAL_LEDGER_READY", True)
    print("PIT_AI_AGENT_ELIGIBILITY_JOIN_READY", True)
    print("PIT_SHARIAH_RL_TRAINING_ENTRYPOINT_READY", True)
    print("READONLY_IBKR_SHADOW_SIZING_ENTRYPOINT_READY", True)
    print("OPERATIONAL_PREFLIGHT_REQUIRED", True)
    print("AUTOMATIC_ATTESTATION", False)
    print("BROKER_SUBMISSION_ENABLED", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
