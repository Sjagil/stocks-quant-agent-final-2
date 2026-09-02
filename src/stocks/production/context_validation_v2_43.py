from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.news.contracts import RawNewsItem
from stocks.news.dedup import cluster_news

from .context_v2_43 import (
    apply_context_policy_v243,
    build_snapshot_v243,
    normalize_economic_event_v243,
    verify_snapshot_v243,
)
from .market_context_pipeline_v2_43 import load_latest_snapshot_v243
from .hydration_guard_v2_43_1 import hydration_guard_v2431


def deterministic_replay_safety_v243(cfg: dict[str, Any]) -> dict[str, bool]:
    cutoff = pd.Timestamp("2026-08-28T14:00:00Z")

    future = normalize_economic_event_v243(
        {
            "id": "CPI-1",
            "type": "CPI",
            "country": "US",
            "currency": "USD",
            "date": "2026-08-28T13:30:00Z",
            "published_at": "2026-08-28T14:01:00Z",
            "forecast": 2.8,
            "actual": 3.1,
        },
        decision_cutoff=cutoff,
        cfg=cfg,
    )
    missing_release_time = normalize_economic_event_v243(
        {
            "id": "CPI-2",
            "type": "CPI",
            "country": "US",
            "date": "2026-08-28T13:30:00Z",
            "forecast": 2.8,
            "actual": 3.1,
        },
        decision_cutoff=cutoff,
        cfg=cfg,
    )
    visible = normalize_economic_event_v243(
        {
            "id": "CPI-3",
            "type": "CPI",
            "country": "US",
            "date": "2026-08-28T13:30:00Z",
            "published_at": "2026-08-28T13:30:02Z",
            "forecast": 2.8,
            "actual": 3.1,
        },
        decision_cutoff=cutoff,
        cfg=cfg,
    )

    now = cutoff.to_pydatetime()
    duplicates = [
        RawNewsItem(
            provider="eodhd",
            provider_id="1",
            published_at=now - timedelta(minutes=10),
            title="Company cuts guidance after weak demand",
            url="https://a.example/1",
            symbols=("AAPL",),
        ),
        RawNewsItem(
            provider="yfinance",
            provider_id="2",
            published_at=now - timedelta(minutes=9),
            title="Company cuts guidance after weak demand",
            url="https://b.example/2",
            symbols=("AAPL",),
        ),
    ]
    duplicate_invariance = len(cluster_news(duplicates)) == 1

    base_snapshot = build_snapshot_v243(
        decision_cutoff=cutoff,
        symbols=["AAPL", "SPY", "QQQ"],
        market_regime={"label": "NEUTRAL"},
        calendar_context={
            "status": "FRESH",
            "entry_blockers": [],
            "calendar_adjustment": 0.0,
        },
        news_context={
            "AAPL": {
                "critical_context_available": True,
                "news_present": True,
                "finbert_ready": True,
                "negative_tail_score": 0.0,
                "event_risk_score": 0.0,
                "sentiment_6h": 1.0,
            }
        },
        data_freshness=[
            {"symbol": "SPY", "status": "FRESH"},
            {"symbol": "QQQ", "status": "FRESH"},
        ],
        provider_provenance=[],
    ).to_dict()
    raw_skip = pd.DataFrame([{
        "symbol": "AAPL",
        "decision": "SKIP",
        "conviction": 0.90,
        "blockers": "",
    }])
    after = apply_context_policy_v243(
        raw_skip,
        snapshot=base_snapshot,
        cfg=cfg,
        agent_shadow=None,
        now=cutoff,
    )
    no_context_entry_creation = str(after.iloc[0]["decision_after_context"]) == "SKIP"

    return {
        "future_actual_hidden": future.actual is None and future.surprise is None,
        "unverified_actual_hidden": (
            missing_release_time.actual is None
            and missing_release_time.surprise is None
        ),
        "visible_actual_allowed": visible.actual == 3.1 and visible.surprise is not None,
        "duplicate_news_invariance": duplicate_invariance,
        "context_cannot_create_entry": no_context_entry_creation,
        "snapshot_hash_verifies": verify_snapshot_v243(base_snapshot),
    }


def context_walk_forward_v243(
    root: str | Path,
    production_cfg: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    root = Path(root).resolve()
    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_43")
    archives = sorted((artifact_root / "decision_archive").glob("CTX-*.csv"))
    provider_root = root / production_cfg["data"]["provider_root"]
    horizon = int(cfg["walk_forward"].get("horizon_bars", 20))
    rows = []

    for archive in archives:
        frame = pd.read_csv(archive)
        for decision in frame.to_dict(orient="records"):
            symbol = str(decision.get("symbol") or "").upper()
            cutoff_raw = decision.get("decision_cutoff")
            if not symbol or not cutoff_raw:
                continue
            data_path = provider_root / f"{symbol}_{production_cfg['data']['timeframe']}.parquet"
            if not data_path.is_file():
                continue
            market = pd.read_parquet(data_path)
            if "timestamp" in market.columns:
                market = market.set_index("timestamp")
            elif "date" in market.columns:
                market = market.set_index("date")
            market.index = pd.to_datetime(market.index, utc=True)
            market = market.sort_index()
            cutoff = pd.Timestamp(cutoff_raw)
            cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
            future = market.loc[market.index > cutoff]
            prior = market.loc[market.index <= cutoff]
            if prior.empty or len(future) < horizon:
                continue
            p0 = float(prior["close"].iloc[-1])
            p1 = float(future["close"].iloc[horizon - 1])
            fwd = p1 / p0 - 1.0
            before = str(decision.get("decision_before_context") or decision.get("decision") or "")
            after = str(decision.get("decision_after_context") or decision.get("decision") or "")
            rows.append({
                "snapshot_id": decision.get("snapshot_id"),
                "symbol": symbol,
                "cutoff": cutoff.isoformat(),
                "forward_return": fwd,
                "context_off_active": before == "BUY_NEW",
                "context_on_active": after == "BUY_NEW",
            })

    off = [row["forward_return"] for row in rows if row["context_off_active"]]
    on = [row["forward_return"] for row in rows if row["context_on_active"]]
    minimum = int(cfg["walk_forward"].get("minimum_observations", 20))
    status = "PASSED" if len(rows) >= minimum and len(off) > 0 else "INSUFFICIENT_HISTORY"
    live_report = {
        "schema": "context_walk_forward_live_archive_v2_43_1",
        "status": status,
        "leakage_safe": True,
        "horizon_bars": horizon,
        "observations": len(rows),
        "minimum_observations": minimum,
        "context_off_active": len(off),
        "context_on_active": len(on),
        "context_off_mean_forward_return": sum(off) / len(off) if off else None,
        "context_on_mean_forward_return": sum(on) / len(on) if on else None,
        "execution_authority": "NONE",
    }

    historical = None
    if status != "PASSED" and bool(cfg["walk_forward"].get("historical_replay_enabled", True)):
        try:
            from .context_replay_v2_43_1 import historical_context_replay_v2431
            historical = historical_context_replay_v2431(root, production_cfg, cfg)
        except Exception as exc:
            historical = {
                "schema": "context_historical_replay_v2_43_1",
                "status": "ERROR",
                "leakage_safe": False,
                "error": f"{type(exc).__name__}:{exc}",
                "observations": 0,
                "execution_authority": "NONE",
            }

    selected = historical if historical and historical.get("status") == "PASSED" else live_report
    report = {
        "schema": "context_walk_forward_v2_43_1",
        "status": selected.get("status", "INSUFFICIENT_HISTORY"),
        "leakage_safe": bool(selected.get("leakage_safe", False)),
        "selected_evidence": (
            "HISTORICAL_CAUSAL_REPLAY"
            if historical and historical.get("status") == "PASSED"
            else "LIVE_DECISION_ARCHIVE"
        ),
        "horizon_bars": horizon,
        "observations": int(selected.get("observations", 0) or 0),
        "minimum_observations": minimum,
        "context_off_active": int(selected.get("context_off_active", 0) or 0),
        "context_on_active": int(selected.get("context_on_active", 0) or 0),
        "context_off_mean_forward_return": selected.get("context_off_mean_forward_return"),
        "context_on_mean_forward_return": selected.get("context_on_mean_forward_return"),
        "live_archive": live_report,
        "historical_replay": historical,
        "execution_authority": "NONE",
    }
    output = root / "artifacts/research_runtime/context_walk_forward_v2_43/summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def context_readiness_v243(
    root: str | Path,
    production_cfg: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Separate machine readiness from whether a BUY happens to exist now."""
    root = Path(root).resolve()
    snapshot = load_latest_snapshot_v243(root, cfg)
    safety = deterministic_replay_safety_v243(cfg)
    walk_path = root / "artifacts/research_runtime/context_walk_forward_v2_43/summary.json"
    walk = (
        json.loads(walk_path.read_text(encoding="utf-8"))
        if walk_path.is_file()
        else {"status": "MISSING", "leakage_safe": False}
    )
    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_43")
    proposal_path = artifact_root / "contextual_proposals.csv"
    proposals = pd.read_csv(proposal_path) if proposal_path.is_file() else pd.DataFrame()

    critical = {str(x).upper() for x in cfg["market_data"].get("critical_symbols", [])}
    fresh = {
        str(row.get("symbol", "")).upper()
        for row in snapshot.get("data_freshness", [])
        if str(row.get("status")) == "FRESH"
    }
    critical_fresh = critical.issubset(fresh)
    audit_columns = {
        "raw_conviction", "calendar_adjustment", "news_adjustment",
        "adjusted_conviction", "decision_before_context",
        "decision_after_context", "context_blockers", "snapshot_id",
    }
    audit_complete = not proposals.empty and audit_columns.issubset(proposals.columns)
    fresh_trigger = (
        bool(
            proposals.get("fresh_entry_trigger", pd.Series(dtype=bool))
            .astype(str).str.lower().isin({"true", "1", "yes"}).any()
        )
        if not proposals.empty else False
    )
    approved_buy = (
        bool(
            proposals.get("decision_after_context", pd.Series(dtype=str))
            .astype(str).eq("BUY_NEW").any()
        )
        if not proposals.empty else False
    )

    calendar_fresh = str(snapshot.get("calendar_context", {}).get("status")) == "FRESH"
    news_context = dict(snapshot.get("news_context") or {})
    critical_news_symbols = {
        str(x).upper() for x in cfg["news"].get("market_context_symbols", ["SPY", "QQQ"])
    }
    critical_news_health = all(
        bool((news_context.get(symbol) or {}).get("critical_context_available", False))
        for symbol in critical_news_symbols
    ) if critical_news_symbols else True

    ppo_zero = float(cfg["rl"].get("ppo_weight", -1)) == 0.0
    sac_shadow = str(cfg["rl"].get("sac_mode")) == "SHADOW_CONTEXT_ONLY"
    rl_direct_false = not bool(cfg["rl"].get("rl_direct_broker_control", True))
    selftests_pass = all(safety.values())
    walk_pass = walk.get("status") == "PASSED" and bool(walk.get("leakage_safe"))

    hydration = hydration_guard_v2431(
        root,
        maximum_age_minutes=float(cfg.get("policy", {}).get("strategy_hydration_max_age_minutes", 180)),
    )
    hydration_fresh = bool(hydration.get("passed"))

    broker_path = root / "artifacts/production_runtime_v2_43_1/broker_snapshot_readonly.json"
    broker = (
        json.loads(broker_path.read_text(encoding="utf-8"))
        if broker_path.is_file()
        else {"status": "MISSING", "healthy": False, "blockers": ["BROKER_SNAPSHOT_MISSING"]}
    )
    broker_healthy = bool(broker.get("healthy")) and int(broker.get("broker_write_calls", 0) or 0) == 0

    system_checks = {
        "replay_no_lookahead": selftests_pass,
        "duplicate_news_invariance": bool(safety["duplicate_news_invariance"]),
        "future_economic_actual_leak_impossible": (
            bool(safety["future_actual_hidden"])
            and bool(safety["unverified_actual_hidden"])
        ),
        "context_on_off_walk_forward_executed": walk_pass,
        "critical_market_data_fresh": critical_fresh,
        "economic_calendar_fresh": calendar_fresh,
        "critical_news_provider_health": critical_news_health,
        "context_audit_trail_complete": audit_complete,
        "strategy_hydration_fresh": hydration_fresh,
        "broker_readonly_snapshot_healthy": broker_healthy,
        "ppo_weight_zero": ppo_zero,
        "sac_shadow_context_only": sac_shadow,
        "rl_direct_broker_control_false": rl_direct_false,
    }
    system_ready = all(system_checks.values())

    dynamic_checks = {
        "fresh_entry_trigger_present": fresh_trigger,
        "context_approved_buy_present": approved_buy,
    }
    entry_eligible_now = system_ready and all(dynamic_checks.values())
    checks = {**system_checks, **dynamic_checks}

    report = {
        "schema": "context_readiness_v2_43_1",
        "status": "SYSTEM_READY_FOR_PAPER" if system_ready else "BLOCKED",
        "system_paper_ready": system_ready,
        "entry_eligible_now": entry_eligible_now,
        "paper_entry_ready": entry_eligible_now,
        "snapshot_id": snapshot["snapshot_id"],
        "checks": checks,
        "system_checks": system_checks,
        "dynamic_entry_checks": dynamic_checks,
        "hydration_guard": hydration,
        "broker_readiness": {
            "status": broker.get("status"),
            "healthy": broker_healthy,
            "blockers": broker.get("blockers", []),
        },
        "selftests": safety,
        "walk_forward": walk,
        "execution_authority": "NONE",
        "broker_submission_enabled": False,
        "order_calls": 0,
    }
    output = artifact_root / "context_readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


__all__ = [
    "context_readiness_v243",
    "context_walk_forward_v243",
    "deterministic_replay_safety_v243",
]
