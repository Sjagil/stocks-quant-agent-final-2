#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.providers.env import load_project_env
from stocks.production.context_portfolio_v2_43 import apply_portfolio_context_v243


def main() -> int:
    load_project_env(ROOT)
    cfg = json.loads((ROOT / "config/market_context_v2_43.json").read_text(encoding="utf-8"))
    result = apply_portfolio_context_v243(ROOT, cfg)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("PRODUCTION_INTELLIGENCE_V2_42_COMPAT_V2_43_OK")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
