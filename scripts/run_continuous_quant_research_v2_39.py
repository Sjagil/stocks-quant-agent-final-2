#!/usr/bin/env python3
from __future__ import annotations
import runpy
import sys
from pathlib import Path

target = Path(__file__).with_name("run_continuous_quant_research_v2_39_2.py")
if not target.is_file():
    raise SystemExit("v2.39.2 evidence-semantic hardened runtime is required but not installed")
print("V2_39_ENTRYPOINT_FORWARDED_TO_V2_39_2", file=sys.stderr)
runpy.run_path(str(target), run_name="__main__")
