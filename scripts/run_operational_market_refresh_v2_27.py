#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime

from pathlib import Path

from stocks.data.current_session_bridge_v2_27 import (
    latest_completed_nyse_session_v227,
)

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)


def _run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--target-usable", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=30)
    args = parser.parse_args()
    as_of = args.as_of or latest_completed_nyse_session_v227(datetime.now(UTC))
    print("RESOLVED_RESEARCH_AS_OF", as_of)

    _run(
        "EODHD_HISTORICAL_HYDRATION",
        [
            str(PYTHON), "scripts/run_contextual_1h_hydration.py",
            "--as-of", as_of,
            "--target-usable", str(args.target_usable),
            "--max-attempts", str(args.max_attempts),
        ],
    )
    _run(
        "IBKR_CURRENT_SESSION_BRIDGE",
        [
            str(PYTHON), "scripts/run_current_session_market_bridge_v2_27.py",
            "--limit", str(args.target_usable),
        ],
    )
    _run(
        "PROVIDER_AND_STOCKS_REFERENCE_FEDERATION",
        [
            str(PYTHON),
            "scripts/run_data_federation_v2_27.py",
            "--as-of", as_of,
            "--limit", str(args.target_usable),
        ],
    )
    _run("CANDIDATE_STRATEGY_MATRIX", [str(PYTHON), "scripts/run_candidate_strategy_matrix.py"])
    _run("DYNAMIC_VALIDATED_DEPLOYMENT", [str(PYTHON), "scripts/run_dynamic_validated_deployment_v2_24.py"])
    _run("DYNAMIC_FORWARD_SIGNAL_ENGINE", [str(PYTHON), "scripts/run_dynamic_forward_signal_engine_v2_24.py"])

    bridge_audit = ROOT / "artifacts/research_runtime/current_session_market_bridge_v2_27/audit.json"
    payload = json.loads(bridge_audit.read_text(encoding="utf-8"))
    print("=" * 100)
    print(
        "OPERATIONAL_MARKET_REFRESH_V2_27",
        "READY", bool(payload.get("all_fresh")),
        "FRESH", payload.get("fresh_count"),
        "BLOCKED", payload.get("blocked_count"),
    )
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
