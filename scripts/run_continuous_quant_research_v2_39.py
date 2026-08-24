#!/usr/bin/env python3
from __future__ import annotations
import runpy,sys
from pathlib import Path
target=Path(__file__).with_name("run_continuous_quant_research_v2_39_1.py")
if not target.is_file():
    raise SystemExit("v2.39.1 hardened runtime is required but not installed")
print("V2_39_ENTRYPOINT_FORWARDED_TO_V2_39_1",file=sys.stderr)
runpy.run_path(str(target),run_name="__main__")
