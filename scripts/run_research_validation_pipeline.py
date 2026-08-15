
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
    args: list[str],
    *,
    required: bool = True,
) -> bool:
    print("=" * 78)
    print("RUN", label)
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
    )
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0 and required:
        raise SystemExit(completed.returncode)
    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--skip-discovery", action="store_true")
    parser.add_argument("--skip-holdout-hydration", action="store_true")
    parser.add_argument("--target-contextual-usable", type=int, default=12)
    parser.add_argument("--max-contextual-attempts", type=int, default=30)
    parser.add_argument("--max-hydration-symbols", type=int, default=24)
    args = parser.parse_args()

    as_of = (
        args.as_of
        or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    )

    if not args.skip_discovery:
        run(
            "PARALLEL_DISCOVERY",
            [
                "scripts/run_parallel_research.py",
                "--limit",
                str(args.limit),
                "--as-of",
                as_of,
            ],
        )

    run(
        "CONTEXTUAL_1H_HYDRATION",
        [
            "scripts/run_contextual_1h_hydration.py",
            "--as-of",
            as_of,
            "--target-usable",
            str(args.target_contextual_usable),
            "--max-attempts",
            str(args.max_contextual_attempts),
        ],
        required=False,
    )

    run(
        "INDICATOR_PYBROKER_CROSSCHECK",
        ["scripts/run_indicator_pybroker_crosscheck.py"],
    )
    run(
        "REGISTRY_PRE_GENERALIZATION",
        ["scripts/build_research_candidate_registry.py"],
    )

    if not args.skip_holdout_hydration:
        run(
            "UNSEEN_1H_HYDRATION",
            [
                "scripts/run_unseen_1h_hydration.py",
                "--as-of",
                as_of,
                "--max-symbols",
                str(args.max_hydration_symbols),
            ],
            required=False,
        )

    run(
        "DYNAMIC_UNIVERSE_GENERALIZATION",
        ["scripts/run_dynamic_universe_generalization.py"],
    )
    run(
        "REGISTRY_POST_GENERALIZATION",
        ["scripts/build_research_candidate_registry.py"],
    )
    run(
        "STRATEGY_REDUNDANCY",
        ["scripts/run_strategy_redundancy_audit.py"],
        required=False,
    )
    run(
        "FINAL_STRATEGY_ROSTER",
        ["scripts/build_final_strategy_roster.py"],
    )
    run(
        "CANDIDATE_STRATEGY_MATRIX",
        ["scripts/run_candidate_strategy_matrix.py"],
    )
    run(
        "RESEARCH_READINESS",
        ["scripts/build_research_readiness.py"],
    )

    print("=" * 78)
    print("RESEARCH_VALIDATION_PIPELINE V2_6 COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
