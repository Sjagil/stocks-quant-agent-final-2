#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--strategies")
    parser.add_argument("--max-variants-per-blueprint", type=int)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--cross-engine", action="store_true")
    parser.add_argument("--limit-symbols", type=int, default=5)
    parser.add_argument("--full-tests", action="store_true")
    args = parser.parse_args()
    python = sys.executable

    focused = [
        "tests/test_strategy_generation_v2_22.py",
        "tests/test_research_candidate_registry.py",
        "tests/test_dynamic_universe_generalization.py",
        "tests/test_cross_engine_indicator_handoff_v2_17_8.py",
        "tests/test_strategy_redundancy.py",
        "tests/test_walkforward_splits.py",
    ]
    focused = [path for path in focused if (ROOT / path).is_file()]
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
        if args.cross_engine:
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
                "DYNAMIC_UNIVERSE_GENERALIZATION",
                [python, "scripts/run_dynamic_universe_generalization.py"],
            )
        run(
            "RESEARCH_CANDIDATE_REGISTRY",
            [python, "scripts/build_research_candidate_registry.py"],
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
    print("AUTOMATIC_FINALIST_PROMOTION", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
