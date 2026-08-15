from __future__ import annotations

import json
from pathlib import Path
from _common import add_repo_src, artifact_ref, base_health, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog", "discovery_context")

def _repo(request: dict) -> Path:
    value = (request.get("context") or {}).get("repo_path")
    if not value:
        raise ValueError("reference repo_path missing")
    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path

def _health(request: dict) -> dict:
    repo = _repo(request); add_repo_src(repo)
    return base_health(request, distributions=(), imports=("stocks.screener.service", "stocks.macro.service", "stocks.research.sec_overlay"), capabilities=CAPABILITIES)

def _catalog(request: dict) -> dict:
    repo = _repo(request)
    return {"state": "OK", "data": {"purpose": "PIT discovery donor with macro scoring and bounded SEC ranking context.", "repo_catalog": repo_catalog(repo, ("src/stocks/screener/*.py", "src/stocks/macro/*.py", "src/stocks/research/sec_overlay.py", "sec_ownership_and_event_intelligence_v1.py"))}}

def _discovery_context(request: dict, artifact_dir: Path) -> dict:
    from collections import Counter
    from dataclasses import replace
    from datetime import date
    repo = _repo(request); add_repo_src(repo)
    from stocks.macro.service import macro_context_at
    from stocks.research.sec_overlay import sec_overlays_for_signals
    from stocks.screener.config import ScreenerConfig
    from stocks.screener.scoring import score_asset
    from stocks.screener.sources import LocalScreenerSources, decision_time_for_session, latest_completed_session
    payload = dict(request.get("payload") or {})
    raw_as_of = payload.get("as_of")
    screening_date = date.fromisoformat(str(raw_as_of)) if raw_as_of else latest_completed_session()
    limit = int(payload.get("limit", 150)); minimum_total_score = float(payload.get("minimum_total_score", 45.0))
    if not 1 <= limit <= 500: raise ValueError("contextual discovery limit must be in [1, 500]")
    if not 0 <= minimum_total_score <= 100: raise ValueError("minimum_total_score must be in [0, 100]")
    config = ScreenerConfig.load(repo); decision_time = decision_time_for_session(screening_date)
    with LocalScreenerSources(repo, config) as sources:
        snapshots = sources.load(screening_date, known_at=decision_time)
        macro_context = macro_context_at(repo, as_of=decision_time)
        scored = [score_asset(replace(snapshot), screening_date=screening_date, config=config, macro_context=macro_context, known_at=decision_time) for snapshot in snapshots]
        records = [item.public for item in scored]; source_inventory = dict(sources.source_inventory)
    classification_counts = Counter(str(row.get("classification")) for row in records)
    eligible = [dict(row) for row in records if not (row.get("rejection_reasons") or []) and str(row.get("classification")) in {"HIGH_POTENTIAL", "WATCHLIST", "NEUTRAL"} and float(row.get("total_score") or 0.0) >= minimum_total_score]
    sec_inputs = [{"symbol": str(row.get("symbol") or "").upper(), "as_of": decision_time.isoformat(), "base_score": float(row.get("total_score") or 0.0), "base_signal_authorized": str(row.get("classification")) in {"HIGH_POTENTIAL", "WATCHLIST"}} for row in eligible if str(row.get("asset_type") or "").upper() == "STOCK" and str(row.get("symbol") or "").strip()]
    sec_error = None
    try: sec_overlays = sec_overlays_for_signals(repo, sec_inputs)
    except Exception as exc: sec_overlays = {}; sec_error = f"{type(exc).__name__}: {exc}"
    enriched = []
    for row in eligible:
        symbol = str(row.get("symbol") or "").upper(); asset_type = str(row.get("asset_type") or "").upper()
        sec_context = sec_overlays.get(symbol) if asset_type == "STOCK" else None
        if not sec_context:
            sec_context = {"status": "UNAVAILABLE" if asset_type == "STOCK" else "NOT_APPLICABLE_NON_STOCK", "as_of": decision_time.isoformat(), "causal_event_count": 0, "sec_intelligence_score": 0.0, "overlay": {"sec_overlay_points": 0.0, "entry_authorized": False}, "authority": "RANKING_OVERLAY_ONLY", "standalone_entry_allowed": False, "delayed_context_only": True}
        sec_points = float((sec_context.get("overlay") or {}).get("sec_overlay_points", 0.0) or 0.0)
        row["source_classification"] = str(row.get("classification")); row["sec_context"] = sec_context
        row["contextual_score"] = max(0.0, min(100.0, float(row.get("total_score") or 0.0) + sec_points))
        row["execution_authority"] = "NONE"; row["broker_calls"] = 0; row["order_calls"] = 0; enriched.append(row)
    enriched.sort(key=lambda row: (float(row.get("contextual_score") or 0.0), float(row.get("total_score") or 0.0), float(row.get("technical_score") or 0.0), str(row.get("symbol") or "")), reverse=True); enriched = enriched[:limit]
    output = artifact_dir / "stocks_reference_contextual_candidates_v2.json"
    artifact = {"schema": "stocks_reference_contextual_candidates_v2", "screening_date": screening_date.isoformat(), "decision_time": decision_time.isoformat(), "screened_count": int(len(records)), "research_pool_count": int(len(eligible)), "candidate_count": int(len(enriched)), "classification_counts": dict(sorted(classification_counts.items())), "research_pool_classifications": ["HIGH_POTENTIAL", "WATCHLIST", "NEUTRAL"], "minimum_total_score": minimum_total_score, "records": enriched, "source_inventory": source_inventory, "macro_regime": (macro_context.get("regime") or {}).get("overall_macro_regime", "UNKNOWN"), "macro_data_status": (macro_context.get("data_quality") or {}).get("status", "DATA_INCOMPLETE"), "sec_error": sec_error, "sec_overlay_bound_points": 4.0, "sec_standalone_entry_allowed": False, "selection_hidden_optimization": False, "execution_authority": "NONE", "strategy_authority": "NONE", "broker_calls": 0, "order_calls": 0}
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"state": "OK", "data": {"screened_count": len(records), "research_pool_count": len(eligible), "candidate_count": len(enriched), "macro_regime": artifact["macro_regime"], "macro_data_status": artifact["macro_data_status"], "sec_error": sec_error, "execution_authority": "NONE"}, "artifacts": [artifact_ref(output, media_type="application/json", rows=len(enriched))], "warnings": [sec_error] if sec_error else []}

def handle(request: dict, artifact_dir: Path) -> dict:
    action = request.get("action")
    if action == "health": return _health(request)
    if action == "catalog": return _catalog(request)
    if action == "discovery_context": return _discovery_context(request, artifact_dir)
    raise ValueError(f"unsupported action: {action}")

if __name__ == "__main__": run_worker(handle)
