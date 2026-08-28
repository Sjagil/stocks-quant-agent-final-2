#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.production.intelligence_v2_42 import run_production_intelligence_v242

def main() -> int:
    cfg = json.loads((ROOT / "config/production_intelligence_v2_42.json").read_text())
    result = run_production_intelligence_v242(ROOT, cfg)
    print(json.dumps(result, indent=2, default=str))
    print("PRODUCTION_INTELLIGENCE_V2_42_OK")
    print("EXECUTION_AUTHORITY NONE")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
