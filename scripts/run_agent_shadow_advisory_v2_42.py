#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.learning.agent_shadow_v2_42 import run_agent_shadow_v242
if __name__ == "__main__":
    result = run_agent_shadow_v242(ROOT)
    print(json.dumps(result, indent=2, default=str))
    print("AGENT_SHADOW_V2_42_OK")
    print("DIRECT_BROKER_CONTROL False")
