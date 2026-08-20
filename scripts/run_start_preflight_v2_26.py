#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from stocks.orchestration.start_preflight_v2_26 import build_start_preflight_from_project_v226

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/operational_start_preflight_v2_26"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-time", default=datetime.now(UTC).isoformat())
    args = parser.parse_args()
    now = datetime.fromisoformat(args.decision_time.replace("Z", "+00:00"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    audit = build_start_preflight_from_project_v226(ROOT, decision_time=now)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print("OPERATIONAL_START_PREFLIGHT_V2_26", "START_READY", audit.get("start_ready"))
    print("BLOCKERS", "|".join(audit.get("blockers") or ["NONE"]))
    print("EXPECTED_LATEST_CLOSED_1H_BAR", audit.get("expected_latest_closed_1h_bar"))
    print("LATEST_DYNAMIC_SIGNAL_BAR", audit.get("latest_dynamic_signal_bar"))
    print("SHARIAH_VERIFIED_DYNAMIC_CANDIDATES", audit.get("shariah_verified_dynamic_candidates", 0))
    print("BROKER_SUBMISSION_ENABLED", False)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", OUTPUT)
    return 0 if audit.get("start_ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
