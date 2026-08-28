#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.learning.mappo_dataset_v2_42 import build_mappo_dataset_v242
if __name__ == "__main__":
    result = build_mappo_dataset_v242(ROOT)
    print(json.dumps(result, indent=2))
    print("MAPPO_DATASET_V2_42_READY")
    print("EXECUTION_AUTHORITY NONE")
