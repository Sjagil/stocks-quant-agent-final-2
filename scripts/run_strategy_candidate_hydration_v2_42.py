#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.production.strategy_hydration_v2_42 import hydrate_strategy_candidates_v242

def main() -> int:
    pcfg = json.loads((ROOT / "config/production_runtime_v2_41.json").read_text())
    icfg = json.loads((ROOT / "config/production_intelligence_v2_42.json").read_text())
    result = hydrate_strategy_candidates_v242(ROOT, pcfg, icfg)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "SUCCEEDED" else 2
if __name__ == "__main__":
    raise SystemExit(main())
