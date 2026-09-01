#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.orchestration.forward_signal_engine import build_forward_signal_state
from stocks.production.hydration_guard_v2_43_1 import hydration_guard_v2431


def main() -> int:
    guard = hydration_guard_v2431(ROOT)
    frame, audit = build_forward_signal_state(ROOT)

    if not guard.get("passed"):
        if not frame.empty:
            frame = frame.copy()
            frame["new_entry_ready"] = False
            frame["fresh_trigger_reason"] = "STRATEGY_HYDRATION_NOT_FRESH"
            frame["production_hydration_guard"] = str(guard.get("reason"))
        audit = {
            **audit,
            "new_entry_ready": 0,
            "production_hydration_guard_passed": False,
            "production_hydration_guard": guard,
            "production_entry_authority": "BLOCKED",
        }
    else:
        audit = {
            **audit,
            "production_hydration_guard_passed": True,
            "production_hydration_guard": guard,
            "production_entry_authority": "RESEARCH_SIGNAL_ONLY",
        }

    output = ROOT / "artifacts/research_runtime/forward_signal_state"
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "signals.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        "FORWARD_SIGNAL_ENGINE_V2_8",
        "ROWS", int(audit.get("rows", 0)),
        "NEW_ENTRY_READY", int(audit.get("new_entry_ready", 0)),
        "ACTIVE_POSITION_STATES", int(audit.get("active_research_positions", 0)),
        "HYDRATION_GUARD", "PASS" if guard.get("passed") else "BLOCKED",
    )
    if not frame.empty:
        columns = [
            "symbol", "strategy", "research_lane", "forward_state",
            "fresh_trigger_reason", "signal_bar_time", "bars_since_entry",
            "applicability_score", "new_entry_ready",
            "position_management_candidate", "production_hydration_guard",
        ]
        print(frame[[c for c in columns if c in frame.columns]].head(60).to_string(index=False))
    print("ARTIFACT_ROOT", output)
    # Returning non-zero makes the causal production chain stop. The artifact is
    # still overwritten with new_entry_ready=False, so a user manually running
    # later scripts cannot accidentally reuse a stale BUY trigger.
    return 0 if guard.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
