#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.reference_macro_v2_43_1 import collect_reference_macro_v2431


def main() -> int:
    result = collect_reference_macro_v2431(ROOT, cutoff=pd.Timestamp.now(tz="UTC"))
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("REFERENCE_STOCKS_MACRO_V2_43_1", result.get("status"))
    return 0 if result.get("status") in {"FRESH", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
