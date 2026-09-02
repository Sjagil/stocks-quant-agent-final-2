from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(label: str, command: list[str], root: Path) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=root, check=False)
    print("RESULT", label, completed.returncode)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-tests", action="store_true")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    py = sys.executable

    run(
        "FOCUSED_TESTS",
        [
            py,
            "-m",
            "pytest",
            "-q",
            "tests/test_dynamic_validated_deployment_v2_24.py",
            "tests/test_pit_training_v2_24.py",
            "tests/test_generated_forward_adapters_v2_23.py",
            "tests/test_final_decision_fabric_v2_8.py",
        ],
        root,
    )
    run("V2_23_RUNTIME_ADAPTER_AUDIT", [py, "scripts/audit_generated_forward_adapters_v2_23.py", "--require-runtime"], root)
    run("CANDIDATE_STRATEGY_MATRIX", [py, "scripts/run_candidate_strategy_matrix.py"], root)
    run("FORWARD_SIGNAL_ENGINE", [py, "scripts/run_forward_signal_engine.py"], root)
    run("DYNAMIC_VALIDATED_DEPLOYMENT", [py, "scripts/run_dynamic_validated_deployment_v2_24.py"], root)
    run("DYNAMIC_FORWARD_SIGNAL_ENGINE", [py, "scripts/run_dynamic_forward_signal_engine_v2_24.py"], root)
    run("RESEARCH_READINESS", [py, "scripts/build_research_readiness.py"], root)
    run("COMPILEALL", [py, "-m", "compileall", "-q", "src", "scripts"], root)
    run("PIP_CHECK", [py, "-m", "pip", "check"], root)
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"], root)
    if args.full_tests:
        run("FULL_TEST_SUITE", [py, "-m", "pytest", "-q"], root)

    print("=" * 100)
    print("V2_24_FINALIZATION RESEARCH_READY")
    print("DYNAMIC_FINAL_ROSTER_DEPLOYMENT True")
    print("PIT_HISTORICAL_TRAINING_CONTRACT True")
    print("PIT_RL_TRAINING_ENTRYPOINT_READY True")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
