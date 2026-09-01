from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


MARKER_RELATIVE = "artifacts/production_runtime_v2_43_1/strategy_hydration.json"


def write_hydration_marker_v2431(root: str | Path, result: dict[str, Any]) -> Path:
    root = Path(root).resolve()
    path = root / MARKER_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC")
    rows = list(result.get("symbols") or [])
    payload = {
        "schema": "strategy_hydration_guard_v2_43_1",
        "status": str(result.get("status") or "FAILED"),
        "generated_at": now.isoformat(),
        "selected_symbols": list(result.get("selected_symbols") or []),
        "successes": int(result.get("successes", 0) or 0),
        "failures": int(result.get("failures", 0) or 0),
        "all_symbol_statuses": {
            str(row.get("symbol") or "").upper(): str(row.get("status") or "UNKNOWN")
            for row in rows if row.get("symbol")
        },
        "broker_write_calls": int(result.get("broker_write_calls", 0) or 0),
        "execution_authority": "NONE",
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def hydration_guard_v2431(
    root: str | Path,
    *,
    maximum_age_minutes: float = 180.0,
) -> dict[str, Any]:
    root = Path(root).resolve()
    path = root / MARKER_RELATIVE
    if not path.is_file():
        return {"passed": False, "reason": "STRATEGY_HYDRATION_MARKER_MISSING", "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stamp = pd.Timestamp(data.get("generated_at"))
        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
    except Exception as exc:
        return {"passed": False, "reason": f"STRATEGY_HYDRATION_MARKER_INVALID:{type(exc).__name__}", "path": str(path)}
    age = (pd.Timestamp.now(tz="UTC") - stamp).total_seconds() / 60.0
    if age < 0 or age > float(maximum_age_minutes):
        return {"passed": False, "reason": "STRATEGY_HYDRATION_MARKER_STALE", "age_minutes": age, "path": str(path)}
    if str(data.get("status")) != "SUCCEEDED" or int(data.get("failures", 1)) != 0:
        return {"passed": False, "reason": "STRATEGY_HYDRATION_FAILED", "age_minutes": age, "path": str(path), "marker": data}
    if int(data.get("broker_write_calls", 0)) != 0:
        return {"passed": False, "reason": "STRATEGY_HYDRATION_WRITE_CALLS_NONZERO", "path": str(path)}
    return {"passed": True, "reason": "STRATEGY_HYDRATION_FRESH", "age_minutes": age, "path": str(path), "marker": data}


__all__ = ["MARKER_RELATIVE", "hydration_guard_v2431", "write_hydration_marker_v2431"]
