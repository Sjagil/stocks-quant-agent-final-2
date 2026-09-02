#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.hydration_guard_v2_43_1 import write_hydration_marker_v2431
from stocks.production.strategy_hydration_v2_42 import hydrate_strategy_candidates_v242


def main() -> int:
    pcfg = json.loads((ROOT / "config/production_runtime_v2_41.json").read_text())
    icfg = json.loads((ROOT / "config/production_intelligence_v2_42.json").read_text())
    try:
        result = hydrate_strategy_candidates_v242(ROOT, pcfg, icfg)
    except Exception as exc:
        result = {
            "status": "FAILED",
            "reason": f"{type(exc).__name__}:{exc}",
            "selected_symbols": [],
            "successes": 0,
            "failures": 1,
            "symbols": [],
            "broker_write_calls": 0,
            "execution_authority": "NONE",
        }
    marker = write_hydration_marker_v2431(ROOT, result)
    result["hydration_marker"] = str(marker)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "SUCCEEDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
