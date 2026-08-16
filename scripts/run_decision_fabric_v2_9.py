#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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

    print(
        "RESULT",
        label,
        completed.returncode,
    )

    if (
        completed.returncode != 0
        and required
    ):
        raise SystemExit(
            completed.returncode
        )

    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        required=True,
    )
    parser.add_argument(
        "--shariah-limit",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--skip-sec",
        action="store_true",
    )
    parser.add_argument(
        "--skip-ibkr",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.skip_sec:
        run(
            "SEC_ACCESS_PREFLIGHT",
            [
                "scripts/"
                "check_sec_access_v2_9.py"
            ],
            required=False,
        )

        run(
            "SHARIAH_FINANCIAL_VERIFICATION",
            [
                "scripts/"
                "run_shariah_financial_verification.py",
                "--as-of",
                args.as_of,
                "--limit",
                str(args.shariah_limit),
            ],
            required=False,
        )

    run(
        "FORWARD_SIGNAL_ENGINE",
        [
            "scripts/"
            "run_forward_signal_engine.py"
        ],
    )

    run(
        "PORTFOLIO_DECISION",
        [
            "scripts/"
            "run_portfolio_decision_v2.py"
        ],
    )

    if not args.skip_ibkr:
        run(
            "IBKR_READONLY_SNAPSHOT",
            [
                "scripts/"
                "run_ibkr_readonly_snapshot_v2_9.py"
            ],
            required=False,
        )

    run(
        "WHOLE_SHARE_SIZING",
        [
            "scripts/"
            "run_whole_share_sizing_v2_9.py"
        ],
        required=False,
    )

    run(
        "AUTONOMY_READINESS_V2_9",
        [
            "scripts/"
            "build_autonomy_readiness_v2_9.py"
        ],
    )

    print("=" * 78)
    print(
        "DECISION_FABRIC V2_9 COMPLETE"
    )
    print(
        "BROKER_ORDER_SUBMISSION",
        "DISABLED",
    )
    print(
        "EXECUTION_AUTHORITY",
        "NONE",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
