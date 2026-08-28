#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.providers.env import load_project_env
from stocks.production.market_context_pipeline_v2_43 import build_market_context_snapshot_v243


def main() -> int:
    load_project_env(ROOT)
    production = json.loads((ROOT / "config/production_runtime_v2_41.json").read_text(encoding="utf-8"))
    context = json.loads((ROOT / "config/market_context_v2_43.json").read_text(encoding="utf-8"))
    result = build_market_context_snapshot_v243(ROOT, production, context)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("MARKET_CONTEXT_SNAPSHOT_V2_43_OK")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
