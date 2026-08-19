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
) -> bool:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0 and required:
        raise SystemExit(completed.returncode)
    return completed.returncode == 0


def validation_queue_state(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "VALIDATION_QUEUE_MISSING"
    try:
        queue = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return False, "NO_CANDIDATE_SURVIVED"
    if queue.empty:
        return False, "NO_CANDIDATE_SURVIVED"
    if "hypothesis_id" not in queue:
        return False, "VALIDATION_QUEUE_SCHEMA_INVALID"
    return True, "READY"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--strategies")
    parser.add_argument("--max-variants-per-blueprint", type=int)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--cross-engine", action="store_true")
    parser.add_argument("--limit-symbols", type=int, default=5)
    parser.add_argument("--full-tests", action="store_true")
    parser.add_argument("--as-of")
    parser.add_argument("--skip-holdout-hydration", action="store_true")
    parser.add_argument("--max-hydration-symbols", type=int, default=24)
    args = parser.parse_args()
    python = sys.executable

    focused = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*v2_22*.py")
    }
    focused.update(
        {
            "tests/test_research_candidate_registry.py",
            "tests/test_dynamic_universe_generalization.py",
            "tests/test_cross_engine_indicator_handoff_v2_17_8.py",
            "tests/test_final_research_fabric.py",
            "tests/test_strategy_redundancy.py",
            "tests/test_walkforward_splits.py",
        }
    )
    focused = sorted(path for path in focused if (ROOT / path).is_file())
    run("FOCUSED_TESTS", [python, "-m", "pytest", "-q", *focused])
    run("COMPILEALL", [python, "-m", "compileall", "-q", "src", "scripts"])
    run("PIP_CHECK", [python, "-m", "pip", "check"])
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"])
    if args.full_tests:
        run("FULL_TEST_SUITE", [python, "-m", "pytest", "-q"])

    command = [python, "scripts/run_strategy_generation_v2_22.py"]
    if args.symbols:
        command.extend(["--symbols", args.symbols])
    if args.strategies:
        command.extend(["--strategies", args.strategies])
    if args.max_variants_per_blueprint:
        command.extend(
            [
                "--max-variants-per-blueprint",
                str(args.max_variants_per_blueprint),
            ]
        )
    if args.catalog_only:
        command.append("--catalog-only")
    run("STRATEGY_GENERATION", command)
    if not args.catalog_only:
        run(
            "STRATEGY_GENERATION_AUDIT",
            [python, "scripts/audit_strategy_generation_v2_22.py"],
        )
        run(
            "REGISTRY_PRE_CROSS_ENGINE",
            [python, "scripts/build_research_candidate_registry.py"],
        )
        if args.cross_engine:
            queue_path = (
                ROOT / "artifacts/research_runtime/strategy_generation_v2_22/"
                "validation_queue.csv"
            )
            ready, reason = validation_queue_state(queue_path)
            if not ready:
                print("=" * 100)
                print("V2_22_FINALIZATION", "CROSS_ENGINE_READY", False)
                print("REASON", reason)
                print("AUTOMATIC_FINALIST_PROMOTION", False)
                print("AUTOMATIC_LIVE_PROMOTION", False)
                print("BROKER_CALLS", 0)
                print("ORDER_CALLS", 0)
                print("EXECUTION_AUTHORITY", "NONE")
                return 3
            scope = (
                ROOT / "artifacts/research_runtime/strategy_generation_v2_22/"
                "cross_engine_scope.yaml"
            )
            cross_output = (
                ROOT / "artifacts/research_runtime/strategy_generation_v2_22/"
                "cross_engine"
            )
            run(
                "BUILD_CROSS_ENGINE_SCOPE",
                [python, "scripts/build_cross_engine_scope_v2_22.py"],
            )
            run(
                "CROSS_ENGINE_VALIDATION",
                [
                    python,
                    "scripts/run_cross_engine_strategy_validation_v2_17.py",
                    "--config",
                    str(scope),
                    "--output-root",
                    str(cross_output),
                    "--limit-symbols",
                    str(args.limit_symbols),
                ],
            )
            run(
                "REGISTRY_POST_CROSS_ENGINE",
                [python, "scripts/build_research_candidate_registry.py"],
            )
            if not args.skip_holdout_hydration:
                as_of = args.as_of or pd.Timestamp.now(tz="UTC").strftime(
                    "%Y-%m-%d"
                )
                run(
                    "UNSEEN_1H_HYDRATION",
                    [
                        python,
                        "scripts/run_unseen_1h_hydration.py",
                        "--as-of",
                        as_of,
                        "--max-symbols",
                        str(max(args.max_hydration_symbols, 0)),
                    ],
                    required=False,
                )
            run(
                "DYNAMIC_UNIVERSE_GENERALIZATION",
                [python, "scripts/run_dynamic_universe_generalization.py"],
            )
            run(
                "REGISTRY_POST_GENERALIZATION",
                [python, "scripts/build_research_candidate_registry.py"],
            )
            run(
                "STRATEGY_REDUNDANCY",
                [python, "scripts/run_strategy_redundancy_audit.py"],
            )
            run(
                "FINAL_STRATEGY_ROSTER",
                [python, "scripts/build_final_strategy_roster.py"],
            )
            run(
                "GENERATED_STRATEGY_PIPELINE_AUDIT",
                [python, "scripts/audit_generated_strategy_pipeline_v2_22.py"],
            )

    print("=" * 100)
    print(
        "V2_22_FINALIZATION", "CATALOG_READY" if args.catalog_only else "RESEARCH_READY"
    )
    print("STRICT_WALK_FORWARD", True)
    print("FAMILY_DIVERSITY_CONTROL", True)
    print("REDUNDANCY_CONTROL", True)
    print("CROSS_ENGINE_REQUESTED", args.cross_engine)
    print(
        "DYNAMIC_UNIVERSE_REQUESTED",
        args.cross_engine,
    )
    print("PIPELINE_EVIDENCE_AUDITED", args.cross_engine)
    print("AUTOMATIC_FINALIST_PROMOTION", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
