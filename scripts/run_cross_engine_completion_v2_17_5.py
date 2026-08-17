#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "artifacts/research_runtime/"
    "cross_engine_completion_v2_17_5"
)


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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-symbols", type=int, default=5)
    parser.add_argument("--skip-full-tests", action="store_true")
    parser.add_argument("--bootstrap-lean", action="store_true")
    parser.add_argument("--require-validation", action="store_true")
    args = parser.parse_args()

    python = sys.executable

    focused = [
        "tests/test_cross_engine_completion_v2_17_5.py",
        "tests/test_cross_engine_runtime_v2_17_4.py",
        "tests/test_cross_engine_fill_parity_v2_17_3.py",
        "tests/test_cross_engine_adapter_compat_v2_17_2.py",
        "tests/test_cross_engine_strategy_validation_v2_17.py",
        "tests/test_stocks_donor_integration_v2_17_1.py",
    ]

    run(
        "FOCUSED_TESTS",
        [python, "-m", "pytest", "-q", *focused],
    )

    if not args.skip_full_tests:
        run(
            "FULL_TEST_SUITE",
            [python, "-m", "pytest", "-q"],
        )

    run("PIP_CHECK", [python, "-m", "pip", "check"])
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
    run("GIT_DIFF_CHECK", ["git", "diff", "--check"])

    run(
        "STOCKS_DONOR_AUDIT",
        [
            python,
            "scripts/audit_stocks_donor_integration_v2_17_1.py",
        ],
    )

    if args.bootstrap_lean:
        run(
            "LEAN_BOOTSTRAP",
            [
                python,
                "scripts/setup_lean_runtime_v2_17_4.py",
                "--install-cli",
                "--build-launcher",
            ],
            required=False,
        )
    else:
        run(
            "LEAN_RUNTIME_PROBE",
            [
                python,
                "scripts/setup_lean_runtime_v2_17_4.py",
            ],
            required=False,
        )

    run(
        "CROSS_ENGINE_RUNTIME",
        [
            python,
            "scripts/audit_cross_engine_runtime_v2_17.py",
        ],
        required=False,
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
        "CROSS_ENGINE_DEEP_AUDIT",
        [
            python,
            "scripts/audit_cross_engine_outputs_v2_17_4.py",
        ],
    )

    root = (
        ROOT
        / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17"
    )
    engines = read_csv(root / "engine_results.csv")
    strategies = read_csv(root / "strategy_summary.csv")

    validated = 0
    blockers: list[str] = []
    if not strategies.empty and "status" in strategies.columns:
        validated = int(
            (
                strategies["status"]
                == "CROSS_ENGINE_VALIDATED"
            ).sum()
        )
        if "blockers" in strategies.columns:
            blockers = [
                str(value)
                for value in strategies["blockers"]
                .dropna()
                .tolist()
            ]

    engine_state = []
    if not engines.empty:
        for row in engines.to_dict(orient="records"):
            engine_state.append(
                {
                    "engine": row.get("engine"),
                    "mode": row.get("mode"),
                    "parity": (
                        bool(row.get("parity"))
                        if pd.notna(row.get("parity"))
                        else False
                    ),
                    "trades": (
                        None
                        if pd.isna(row.get("trades"))
                        else int(row.get("trades"))
                    ),
                    "error": (
                        None
                        if pd.isna(row.get("error"))
                        else str(row.get("error"))
                    ),
                    "warnings": (
                        None
                        if pd.isna(row.get("warnings"))
                        else str(row.get("warnings"))
                    ),
                }
            )

    OUT.mkdir(parents=True, exist_ok=True)
    audit = {
        "schema": "cross_engine_completion_v2_17_5",
        "pipeline_executed": True,
        "strategies_evaluated": int(len(strategies)),
        "strategies_validated": validated,
        "cross_engine_validated": bool(validated > 0),
        "engine_state": engine_state,
        "blockers": blockers,
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "fixed_euro_order_cap": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (OUT / "audit.json").write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 100)
    print("CROSS_ENGINE_COMPLETION_V2_17_5")
    print("PIPELINE_EXECUTED True")
    print("STRATEGIES_EVALUATED", len(strategies))
    print("STRATEGIES_VALIDATED", validated)
    print("CROSS_ENGINE_VALIDATED", bool(validated > 0))
    print("WHOLE_SHARES_ONLY True")
    print("FIXED_EURO_ORDER_CAP False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", OUT)

    if args.require_validation and validated == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
