#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.context_replay_v2_43_1 import historical_context_replay_v2431


def main() -> int:
    production = json.loads((ROOT / "config/production_runtime_v2_41.json").read_text(encoding="utf-8"))
    context = json.loads((ROOT / "config/market_context_v2_43.json").read_text(encoding="utf-8"))
    result = historical_context_replay_v2431(ROOT, production, context)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("CONTEXT_HISTORICAL_REPLAY_V2_43_1", result.get("status"))
    print("EXECUTION_AUTHORITY NONE")
    return 0 if result.get("status") == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
