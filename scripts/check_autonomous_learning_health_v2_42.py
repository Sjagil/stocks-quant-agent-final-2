#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.learning.config_v2_40 import load_learning_config_v240, resolve_runtime_paths_v240

def pid_alive(pid):
    try:
        os.kill(int(pid), 0); return True
    except Exception:
        return False

if __name__ == "__main__":
    cfg = load_learning_config_v240(ROOT)
    paths = resolve_runtime_paths_v240(ROOT, cfg)
    report = paths["reports"] / "latest_cycle.json"
    lock = paths["lock"]
    lock_pid = None
    if lock.is_file():
        try: lock_pid = int(lock.read_text().strip().splitlines()[0])
        except Exception: pass
    age = None if not report.is_file() else max(0.0, time.time() - report.stat().st_mtime)
    max_age = max(1800, int(cfg.get("runtime", {}).get("cycle_seconds", 900)) * 3)
    payload = {
        "lock_present": lock.is_file(), "lock_pid": lock_pid,
        "lock_pid_alive": bool(lock_pid and pid_alive(lock_pid)),
        "latest_cycle_report": str(report), "latest_cycle_age_seconds": age,
        "latest_cycle_recent": age is not None and age <= max_age,
        "healthy": bool(lock_pid and pid_alive(lock_pid) and age is not None and age <= max_age),
        "execution_authority": "NONE",
    }
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if payload["healthy"] else 2)
