from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from _common import add_repo_src, artifact_ref, base_health, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog", "discovery_context", "market_context")

RESEARCH_SOFT_BLOCKERS = frozenset(
    {
        "SHARIAH_DATA_UNAVAILABLE",
        "SHARIAH_DATA_INCOMPLETE",
        "MISSING_FUNDAMENTAL_DATA",
        "MISSING_FUNDAMENTAL_TIMESTAMP",
        "STALE_FUNDAMENTAL_DATA",
        "MISSING_CRITICAL_FUNDAMENTAL_DATA",
        "INSUFFICIENT_FUNDAMENTAL_COVERAGE",
        "NON_POSITIVE_EARNINGS_AND_FCF",
        "MISSING_BENCHMARK_DATA",
        "INSUFFICIENT_VOLUME",
        "INSUFFICIENT_DOLLAR_VOLUME",
        "EXTREME_BID_ASK_SPREAD",
        "EXTREME_VOLATILITY",
        "EXTREME_OVEREXTENSION",
        "MICRO_CAP_BLOCKED",
    }
)
FUNDAMENTAL_DATA_BLOCKERS = frozenset(
    {
        "MISSING_FUNDAMENTAL_DATA",
        "MISSING_FUNDAMENTAL_TIMESTAMP",
        "STALE_FUNDAMENTAL_DATA",
        "MISSING_CRITICAL_FUNDAMENTAL_DATA",
        "INSUFFICIENT_FUNDAMENTAL_COVERAGE",
    }
)
VERIFIED_SHARIAH = frozenset({"SHARIAH_COMPLIANT", "SHARIAH_ELIGIBLE_PIT"})
PENDING_SHARIAH = frozenset({"SHARIAH_DATA_UNAVAILABLE", "SHARIAH_DATA_INCOMPLETE"})


def _repo(request: dict) -> Path:
    value = (request.get("context") or {}).get("repo_path")
    if not value:
        raise ValueError("reference repo_path missing")
    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def _health(request: dict) -> dict:
    repo = _repo(request)
    add_repo_src(repo)
    return base_health(
        request,
        distributions=(),
        imports=(
            "stocks.screener.service",
            "stocks.macro.service",
            "stocks.research.sec_overlay",
        ),
        capabilities=CAPABILITIES,
    )


def _catalog(request: dict) -> dict:
    repo = _repo(request)
    return {
        "state": "OK",
        "data": {
            "purpose": (
                "PIT discovery donor with separate research/trade eligibility, "
                "macro scoring, and bounded SEC ranking context."
            ),
            "repo_catalog": repo_catalog(
                repo,
                (
                    "src/stocks/screener/*.py",
                    "src/stocks/macro/*.py",
                    "src/stocks/research/sec_overlay.py",
                    "sec_ownership_and_event_intelligence_v1.py",
                ),
            ),
        },
    }


def _shariah_gate(row: dict[str, Any], blockers: list[str]) -> str:
    status = str(row.get("shariah_status") or "").upper()
    if status in VERIFIED_SHARIAH:
        if status in blockers:
            return "REVERIFY"
        return "VERIFIED"
    if status in PENDING_SHARIAH or not status:
        return "PENDING"
    return "BLOCKED"


def _research_blockers(row: dict[str, Any]) -> list[str]:
    blockers = [str(item) for item in (row.get("rejection_reasons") or [])]
    gate = _shariah_gate(row, blockers)
    soft = set(RESEARCH_SOFT_BLOCKERS)
    if gate == "REVERIFY":
        soft.add(str(row.get("shariah_status") or "").upper())
    if gate == "BLOCKED":
        soft.discard(str(row.get("shariah_status") or "").upper())
    return [item for item in blockers if item not in soft]


def _research_score(row: dict[str, Any], config: Any) -> float:
    blockers = set(str(item) for item in (row.get("rejection_reasons") or []))
    components: dict[str, float] = {
        "technical": float(row.get("technical_score") or 0.0),
        "liquidity": float(row.get("liquidity_score") or 0.0),
        "risk": float(row.get("risk_score") or 0.0),
    }
    applicability = str(row.get("fundamental_applicability") or "")
    coverage = float(row.get("fundamental_coverage") or 0.0)
    if (
        applicability == "COMPANY_LEVEL"
        and coverage > 0.0
        and not blockers.intersection(FUNDAMENTAL_DATA_BLOCKERS)
    ):
        components["fundamental"] = float(row.get("fundamental_score") or 0.0)
    macro_score = row.get("macro_score")
    if macro_score not in (None, ""):
        components["macro"] = float(macro_score)
    weights = {key: float(config.weights[key]) for key in components}
    denominator = sum(weights.values())
    if denominator <= 0:
        return 0.0
    return round(
        sum(components[key] * weights[key] for key in components) / denominator,
        4,
    )


def _discovery_context(request: dict, artifact_dir: Path) -> dict:
    from dataclasses import replace
    from datetime import date

    repo = _repo(request)
    add_repo_src(repo)
    from stocks.macro.service import macro_context_at
    from stocks.research.sec_overlay import sec_overlays_for_signals
    from stocks.screener.config import ScreenerConfig
    from stocks.screener.scoring import score_asset
    from stocks.screener.sources import (
        LocalScreenerSources,
        decision_time_for_session,
        latest_completed_session,
    )

    payload = dict(request.get("payload") or {})
    raw_as_of = payload.get("as_of")
    screening_date = (
        date.fromisoformat(str(raw_as_of)) if raw_as_of else latest_completed_session()
    )
    limit = int(payload.get("limit", 150))
    minimum_total_score = float(payload.get("minimum_total_score", 45.0))
    if not 1 <= limit <= 500:
        raise ValueError("contextual discovery limit must be in [1, 500]")
    if not 0 <= minimum_total_score <= 100:
        raise ValueError("minimum_total_score must be in [0, 100]")

    config = ScreenerConfig.load(repo)
    decision_time = decision_time_for_session(screening_date)
    with LocalScreenerSources(repo, config) as sources:
        snapshots = sources.load(screening_date, known_at=decision_time)
        macro_context = macro_context_at(repo, as_of=decision_time)
        scored = [
            score_asset(
                replace(snapshot),
                screening_date=screening_date,
                config=config,
                macro_context=macro_context,
                known_at=decision_time,
            )
            for snapshot in snapshots
        ]
        records = [dict(item.public) for item in scored]
        source_inventory = dict(sources.source_inventory)

    classification_counts = Counter(str(row.get("classification")) for row in records)
    rejection_reason_counts: Counter[str] = Counter()
    research_blocker_counts: Counter[str] = Counter()
    trade_blocker_counts: Counter[str] = Counter()
    shariah_gate_counts: Counter[str] = Counter()
    eligible: list[dict[str, Any]] = []

    for row in records:
        trade_blockers = [str(item) for item in (row.get("rejection_reasons") or [])]
        for blocker in trade_blockers:
            rejection_reason_counts[blocker] += 1
            trade_blocker_counts[blocker] += 1
        research_blockers = _research_blockers(row)
        for blocker in research_blockers:
            research_blocker_counts[blocker] += 1
        gate = _shariah_gate(row, trade_blockers)
        shariah_gate_counts[gate] += 1
        research_score = _research_score(row, config)
        research_eligible = (
            gate != "BLOCKED"
            and not research_blockers
            and research_score >= minimum_total_score
        )
        row["source_classification"] = str(row.get("classification") or "REJECTED")
        row["trade_blockers"] = trade_blockers
        row["research_blockers"] = research_blockers
        row["trade_eligible"] = not trade_blockers
        row["research_eligible"] = research_eligible
        row["shariah_gate"] = gate
        row["shariah_verification_required"] = gate in {"PENDING", "REVERIFY"}
        row["research_score"] = research_score
        if research_eligible:
            eligible.append(row)

    sec_inputs = [
        {
            "symbol": str(row.get("symbol") or "").upper(),
            "as_of": decision_time.isoformat(),
            "base_score": float(row.get("research_score") or 0.0),
            "base_signal_authorized": bool(row.get("trade_eligible"))
            and str(row.get("source_classification"))
            in {"HIGH_POTENTIAL", "WATCHLIST"},
        }
        for row in eligible
        if str(row.get("asset_type") or "").upper() == "STOCK"
        and str(row.get("symbol") or "").strip()
    ]
    sec_error = None
    try:
        sec_overlays = sec_overlays_for_signals(repo, sec_inputs)
    except Exception as exc:
        sec_overlays = {}
        sec_error = f"{type(exc).__name__}: {exc}"

    enriched: list[dict[str, Any]] = []
    for row in eligible:
        symbol = str(row.get("symbol") or "").upper()
        asset_type = str(row.get("asset_type") or "").upper()
        sec_context = sec_overlays.get(symbol) if asset_type == "STOCK" else None
        if not sec_context:
            sec_context = {
                "status": "UNAVAILABLE" if asset_type == "STOCK" else "NOT_APPLICABLE_NON_STOCK",
                "as_of": decision_time.isoformat(),
                "causal_event_count": 0,
                "sec_intelligence_score": 0.0,
                "overlay": {"sec_overlay_points": 0.0, "entry_authorized": False},
                "authority": "RANKING_OVERLAY_ONLY",
                "standalone_entry_allowed": False,
                "delayed_context_only": True,
            }
        sec_points = float(
            (sec_context.get("overlay") or {}).get("sec_overlay_points", 0.0) or 0.0
        )
        row["sec_context"] = sec_context
        row["contextual_score"] = max(
            0.0,
            min(100.0, float(row.get("research_score") or 0.0) + sec_points),
        )
        row["execution_authority"] = "NONE"
        row["broker_calls"] = 0
        row["order_calls"] = 0
        enriched.append(row)

    enriched.sort(
        key=lambda row: (
            bool(row.get("trade_eligible")),
            float(row.get("contextual_score") or 0.0),
            float(row.get("technical_score") or 0.0),
            str(row.get("symbol") or ""),
        ),
        reverse=True,
    )
    enriched = enriched[:limit]

    output = artifact_dir / "stocks_reference_contextual_candidates_v2.json"
    macro_regime = (macro_context.get("regime") or {}).get(
        "overall_macro_regime", "UNKNOWN"
    )
    macro_data_status = (macro_context.get("data_quality") or {}).get(
        "status", "DATA_INCOMPLETE"
    )
    artifact = {
        "schema": "stocks_reference_contextual_candidates_v2",
        "screening_date": screening_date.isoformat(),
        "decision_time": decision_time.isoformat(),
        "screened_count": int(len(records)),
        "research_pool_count": int(len(eligible)),
        "candidate_count": int(len(enriched)),
        "trade_eligible_count": int(sum(bool(row.get("trade_eligible")) for row in enriched)),
        "classification_counts": dict(sorted(classification_counts.items())),
        "rejection_reason_counts": dict(rejection_reason_counts.most_common()),
        "research_blocker_counts": dict(research_blocker_counts.most_common()),
        "trade_blocker_counts": dict(trade_blocker_counts.most_common()),
        "shariah_gate_counts": dict(sorted(shariah_gate_counts.items())),
        "minimum_research_score": minimum_total_score,
        "research_score_contract": (
            "RENORMALIZED_AVAILABLE_COMPONENT_SCORE; "
            "MISSING_FUNDAMENTALS_ARE_NOT_TREATED_AS_ZERO_ALPHA"
        ),
        "records": enriched,
        "source_inventory": source_inventory,
        "macro_regime": macro_regime,
        "macro_data_status": macro_data_status,
        "sec_error": sec_error,
        "sec_overlay_bound_points": 4.0,
        "sec_standalone_entry_allowed": False,
        "selection_hidden_optimization": False,
        "execution_authority": "NONE",
        "strategy_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {
        "state": "OK",
        "data": {
            "screened_count": len(records),
            "research_pool_count": len(eligible),
            "candidate_count": len(enriched),
            "trade_eligible_count": artifact["trade_eligible_count"],
            "macro_regime": macro_regime,
            "macro_data_status": macro_data_status,
            "sec_error": sec_error,
            "execution_authority": "NONE",
        },
        "artifacts": [
            artifact_ref(output, media_type="application/json", rows=len(enriched))
        ],
        "warnings": [sec_error] if sec_error else [],
    }


def _market_context(request: dict, artifact_dir: Path) -> dict:
    repo = _repo(request)
    add_repo_src(repo)
    from stocks.market.context import MarketContextLayout, build_market_context

    payload = dict(request.get("payload") or {})
    symbols = payload.get("symbols") or ["SPY", "QQQ", "AAPL", "NVDA"]
    result = build_market_context(
        repo,
        symbols=symbols,
        fetch_options=bool(payload.get("fetch_options", True)),
        max_expirations=int(payload.get("max_expirations", 4)),
    )
    layout = MarketContextLayout(repo)
    artifacts = []
    for path, media_type in (
        (layout.gex_json, "application/json"),
        (layout.orderflow_parquet, "application/x-parquet"),
        (layout.status_json, "application/json"),
        (layout.source_audit_json, "application/json"),
    ):
        if path.is_file():
            artifacts.append(artifact_ref(path, media_type=media_type))
    return {
        "state": "OK",
        "data": {
            "status": result.get("status", "GO") if isinstance(result, dict) else "GO",
            "execution_authority": "NONE",
            "broker_calls": 0,
        },
        "artifacts": artifacts,
    }

def handle(request: dict, artifact_dir: Path) -> dict:
    action = request.get("action")
    if action == "health":
        return _health(request)
    if action == "catalog":
        return _catalog(request)
    if action == "discovery_context":
        return _discovery_context(request, artifact_dir)
    if action == "market_context":
        return _market_context(request, artifact_dir)
    raise ValueError(f"unsupported action: {action}")


if __name__ == "__main__":
    run_worker(handle)
