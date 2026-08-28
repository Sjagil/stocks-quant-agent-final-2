#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.context_validation_v2_43 import context_walk_forward_v243


def main() -> int:
    production = json.loads((ROOT / "config/production_runtime_v2_41.json").read_text(encoding="utf-8"))
    context = json.loads((ROOT / "config/market_context_v2_43.json").read_text(encoding="utf-8"))
    result = context_walk_forward_v243(ROOT, production, context)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("CONTEXT_WALK_FORWARD_V2_43", result["status"])
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
