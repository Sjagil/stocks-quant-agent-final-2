
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
    print(
        "=" * 78
    )
    print(
        "RUN",
        label,
    )

    completed = subprocess.run(
        [
            sys.executable,
            *args,
        ],
        cwd=ROOT,
        check=False,
    )

    print(
        "RESULT",
        label,
        completed.returncode,
    )

    if (
        completed.returncode
        != 0
        and required
    ):
        raise SystemExit(
            completed.returncode
        )

    return (
        completed.returncode
        == 0
    )


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
        "--skip-shariah-fetch",
        action="store_true",
    )
    args = parser.parse_args()

    run(
        "MARKET_STRUCTURE_15M_GENERALIZATION",
        [
            "scripts/"
            "run_market_structure_15m_generalization.py"
        ],
        required=False,
    )

    if not args.skip_shariah_fetch:
        run(
            "SHARIAH_FINANCIAL_VERIFICATION",
            [
                "scripts/"
                "run_shariah_financial_verification.py",
                "--as-of",
                args.as_of,
                "--limit",
                str(
                    args.shariah_limit
                ),
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

    run(
        "AUTONOMY_READINESS",
        [
            "scripts/"
            "build_autonomy_readiness_v2_7.py"
        ],
    )

    print(
        "=" * 78
    )
    print(
        "FINAL_DECISION_FABRIC "
        "V2_7 COMPLETE"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
