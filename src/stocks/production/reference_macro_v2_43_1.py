from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env


def _load_fresh(path: Path, ttl_hours: float) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stamp = pd.Timestamp(data.get("retrieved_at"))
        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
        if (pd.Timestamp.now(tz="UTC") - stamp).total_seconds() <= ttl_hours * 3600:
            return data
    except Exception:
        return None
    return None


def collect_reference_macro_v2431(
    root: str | Path,
    *,
    cutoff: Any,
    ttl_hours: float = 6.0,
    lookback_days: int = 450,
) -> dict[str, Any]:
    """Pull the imported Stocks PIT macro engine through its isolated integration.

    This is context-only. It cannot create trades and it is not a replacement for
    the hard economic-event calendar. It contributes FRED/ALFRED, ECB, Eurostat,
    Yahoo/yfinance and the donor repo's own validation/provenance.
    """
    root = Path(root).resolve()
    load_project_env(root)
    cache = root / "artifacts/production_runtime_v2_43_1/reference_macro.json"
    cached = _load_fresh(cache, ttl_hours)
    if cached is not None:
        return {**cached, "cache_hit": True}

    cutoff_ts = pd.Timestamp(cutoff)
    cutoff_ts = cutoff_ts.tz_localize("UTC") if cutoff_ts.tzinfo is None else cutoff_ts.tz_convert("UTC")
    start = (cutoff_ts - pd.Timedelta(days=int(lookback_days))).date().isoformat()
    end = cutoff_ts.date().isoformat()
    registry = IntegrationRegistry.load(root / "config/integrations.yaml", project_root=root)
    runner = IntegrationRunner(registry)
    started = time.monotonic()
    result: dict[str, Any]
    try:
        response = runner.run(
            "stocks_context_reference",
            "macro_refresh_read_only",
            {"start": start, "end": end},
            timeout_seconds=180,
        )
        artifact_data = None
        artifact_path = None
        if response.artifacts:
            artifact_path = Path(response.artifacts[0].path)
            artifact_data = json.loads(artifact_path.read_text(encoding="utf-8"))
        data = dict(getattr(response, "data", {}) or {})
        result = {
            "schema": "reference_macro_v2_43_1",
            "status": "FRESH" if response.ok else "DEGRADED",
            "retrieved_at": cutoff_ts.isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "integration_state": str(getattr(getattr(response, "state", None), "value", getattr(response, "state", "UNKNOWN"))),
            "macro_regime": data.get("latest_regime"),
            "macro_status": data.get("macro_status"),
            "validation_status": data.get("validation_status"),
            "collection_status": data.get("collection_status"),
            "artifact": str(artifact_path) if artifact_path else None,
            "artifact_summary": {
                "validation_status": ((artifact_data or {}).get("validation") or {}).get("status"),
                "latest_regime": ((artifact_data or {}).get("status") or {}).get("latest_regime"),
            },
            "sources": ["Stocks.macro", "FRED/ALFRED", "ECB", "EUROSTAT", "YAHOO/yfinance"],
            "strategy_authority": "NONE",
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
            "cache_hit": False,
        }
    except Exception as exc:
        result = {
            "schema": "reference_macro_v2_43_1",
            "status": "DEGRADED",
            "retrieved_at": cutoff_ts.isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "error": f"{type(exc).__name__}:{exc}",
            "sources": ["Stocks.macro"],
            "strategy_authority": "NONE",
            "execution_authority": "NONE",
            "broker_calls": 0,
            "order_calls": 0,
            "cache_hit": False,
        }
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return result


__all__ = ["collect_reference_macro_v2431"]
