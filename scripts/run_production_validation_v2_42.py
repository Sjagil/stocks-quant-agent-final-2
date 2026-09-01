#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts/run_production_hardening_validation_v2_43_1.py"), run_name="__main__")
