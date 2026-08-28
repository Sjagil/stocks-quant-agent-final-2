from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.news.evidence import build_news_evidence
from stocks.news.nlp import financial_sentiment


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _fetch_json(endpoint: str, params: dict[str, Any], *, timeout: int = 15) -> Any:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{endpoint}?{query}", headers={"User-Agent": "stocks-quant-agent/2.42"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec - fixed HTTPS endpoint
        return json.loads(response.read().decode("utf-8"))


def _api_key() -> str:
    value = os.environ.get("EODHD_API_KEY", "").strip()
    if not value:
        raise RuntimeError("EODHD_API_KEY missing")
    return value


def _provider_id(title: str, link: str) -> str:
    return hashlib.sha256((title + "|" + link).encode("utf-8")).hexdigest()[:24]


def fetch_eodhd_news_v242(symbol: str, *, now: pd.Timestamp, lookback_days: int, limit: int) -> list[dict[str, Any]]:
    start = (now - pd.Timedelta(days=int(lookback_days))).date().isoformat()
    end = now.date().isoformat()
    payload = _fetch_json(
        "https://eodhd.com/api/news",
        {
            "api_token": _api_key(), "fmt": "json", "s": f"{symbol.upper()}.US",
            "from": start, "to": end, "limit": int(limit), "offset": 0,
        },
    )
    if not isinstance(payload, list):
        raise ValueError("EODHD news response is not a list")
    rows: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict) or not raw.get("title") or not raw.get("date"):
            continue
        published = _utc(raw["date"])
        if published > now:
            continue
        title = str(raw.get("title") or "")
        link = str(raw.get("link") or "")
        sentiment = raw.get("sentiment") if isinstance(raw.get("sentiment"), dict) else {}
        rows.append({
            "provider": "eodhd",
            "provider_id": _provider_id(title, link),
            "published_at": published.isoformat(),
            "title": title,
            "url": link,
            "summary": str(raw.get("content") or "")[:4000],
            "source_name": urllib.parse.urlparse(link).netloc,
            "symbols": list(raw.get("symbols") or []),
            "categories": list(raw.get("tags") or []),
            "provider_sentiment": sentiment.get("polarity"),
            "metadata": {"provider_sentiment": sentiment},
        })
    return rows


def fetch_economic_events_v242(*, now: pd.Timestamp, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    macro = cfg["macro"]
    start = (now - pd.Timedelta(days=int(macro.get("lookback_days", 1)))).date().isoformat()
    end = (now + pd.Timedelta(days=int(macro.get("lookahead_days", 2)))).date().isoformat()
    output: list[dict[str, Any]] = []
    for country in macro.get("countries", ["US"]):
        payload = _fetch_json(
            "https://eodhd.com/api/economic-events",
            {
                "api_token": _api_key(), "fmt": "json", "from": start, "to": end,
                "country": str(country), "limit": 1000, "offset": 0,
            },
        )
        if not isinstance(payload, list):
            raise ValueError("EODHD economic-events response is not a list")
        for raw in payload:
            if not isinstance(raw, dict) or not raw.get("date"):
                continue
            row = dict(raw)
            # Provider timestamps are treated as UTC for deterministic causal gating.
            row["event_time"] = _utc(raw["date"]).isoformat()
            output.append(row)
    return sorted(output, key=lambda x: x["event_time"])


def _severity(event_type: str, cfg: dict[str, Any]) -> str:
    text = f" {str(event_type).lower()} "
    macro = cfg["macro"]
    if any(k.lower() in text for k in macro.get("high_impact_keywords", [])):
        return "HIGH"
    if any(k.lower() in text for k in macro.get("medium_impact_keywords", [])):
        return "MEDIUM"
    return "LOW"


def macro_context_v242(events: list[dict[str, Any]], *, now: pd.Timestamp, cfg: dict[str, Any]) -> dict[str, Any]:
    macro = cfg["macro"]
    high_pre = float(macro.get("high_impact_pre_minutes", 90))
    high_post = float(macro.get("high_impact_post_minutes", 30))
    med_pre = float(macro.get("medium_impact_pre_minutes", 60))
    blockers: list[str] = []
    multiplier = 1.0
    relevant: list[dict[str, Any]] = []
    for raw in events:
        event_time = _utc(raw["event_time"])
        delta_min = float((event_time - now).total_seconds() / 60.0)
        severity = _severity(str(raw.get("type") or ""), cfg)
        row = {**raw, "severity": severity, "minutes_from_now": delta_min}
        # Future events: schedule is known, actual is not used before release.
        if event_time > now:
            row["actual"] = None
        relevant.append(row)
        if severity == "HIGH" and -high_post <= delta_min <= high_pre:
            blockers.append("MACRO_HIGH_IMPACT_WINDOW")
        elif severity == "MEDIUM" and 0 <= delta_min <= med_pre:
            multiplier = min(multiplier, float(macro.get("medium_conviction_multiplier", 0.85)))
    return {
        "blockers": sorted(set(blockers)),
        "conviction_multiplier": multiplier,
        "events": relevant,
        "high_impact_window": "MACRO_HIGH_IMPACT_WINDOW" in blockers,
    }


def news_context_v242(symbol: str, rows: list[dict[str, Any]], *, now: pd.Timestamp, cfg: dict[str, Any]) -> dict[str, Any]:
    news_cfg = cfg["news"]
    backend_probe = financial_sentiment("Financial markets are open for trading.")
    finbert_ready = backend_probe.backend == "transformers"
    evidence = build_news_evidence(rows, target_symbol=symbol, now=now.to_pydatetime()) if rows else []
    filtered = [e for e in evidence if float(e.evidence_score) >= float(news_cfg.get("minimum_story_evidence_score", 0.12))]
    denom = sum(float(e.evidence_score) for e in filtered)
    weighted = (
        sum(float(e.evidence_score) * float(e.sentiment) for e in filtered) / denom
        if denom > 0 else 0.0
    )
    strongest_negative = min((float(e.sentiment) for e in filtered), default=0.0)
    max_evidence = max((float(e.evidence_score) for e in filtered), default=0.0)
    blockers: list[str] = []
    if rows and bool(news_cfg.get("require_finbert_for_new_entries", True)) and not finbert_ready:
        blockers.append("NLP_FINBERT_UNAVAILABLE")
    if (
        weighted <= float(news_cfg.get("negative_block_weighted_sentiment", -0.45))
        and max_evidence >= float(news_cfg.get("negative_block_min_evidence", 0.22))
    ):
        blockers.append("NEGATIVE_NEWS_RISK")
    boost = float(news_cfg.get("maximum_positive_conviction_boost", 0.08))
    haircut = float(news_cfg.get("maximum_negative_conviction_haircut", 0.25))
    if weighted >= 0:
        multiplier = 1.0 + min(boost, weighted * boost)
    else:
        multiplier = 1.0 - min(haircut, abs(weighted) * haircut)
    return {
        "symbol": symbol.upper(),
        "finbert_ready": finbert_ready,
        "nlp_backend": backend_probe.backend,
        "stories_raw": len(rows),
        "stories_evidence": len(filtered),
        "weighted_sentiment": weighted,
        "strongest_negative_sentiment": strongest_negative,
        "max_evidence_score": max_evidence,
        "conviction_multiplier": multiplier,
        "blockers": sorted(set(blockers)),
        "top_evidence": [e.to_dict() for e in filtered[:8]],
    }


def apply_production_context_v242(
    proposals: pd.DataFrame,
    *,
    macro: dict[str, Any],
    news_by_symbol: dict[str, dict[str, Any]],
    generated_at: pd.Timestamp,
) -> pd.DataFrame:
    out = proposals.copy()
    if out.empty:
        return out
    rows: list[dict[str, Any]] = []
    for raw in out.to_dict(orient="records"):
        row = dict(raw)
        symbol = str(row.get("symbol") or "").upper()
        news = news_by_symbol.get(symbol, {
            "weighted_sentiment": 0.0, "conviction_multiplier": 1.0,
            "blockers": [], "nlp_backend": "none", "stories_evidence": 0,
        })
        blockers = [x for x in str(row.get("blockers") or "").split("|") if x]
        blockers.extend(macro.get("blockers", []))
        blockers.extend(news.get("blockers", []))
        raw_conv = float(row.get("conviction") or 0.0)
        multiplier = float(macro.get("conviction_multiplier", 1.0)) * float(news.get("conviction_multiplier", 1.0))
        row["conviction_pre_context"] = raw_conv
        row["conviction"] = min(1.0, max(0.0, raw_conv * multiplier))
        row["production_context_multiplier"] = multiplier
        row["production_macro_high_impact_window"] = bool(macro.get("high_impact_window"))
        row["production_news_sentiment"] = float(news.get("weighted_sentiment", 0.0))
        row["production_news_story_count"] = int(news.get("stories_evidence", 0))
        row["production_nlp_backend"] = str(news.get("nlp_backend", "none"))
        row["production_context_generated_at"] = generated_at.isoformat()
        row["blockers"] = "|".join(sorted(set(blockers)))
        rows.append(row)
    return pd.DataFrame(rows)


def run_production_intelligence_v242(root: str | Path, cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    now = pd.Timestamp.now(tz="UTC")
    proposal_path = root / "artifacts/research_runtime/portfolio_decision_v2_7/proposals.csv"
    if not proposal_path.is_file():
        raise FileNotFoundError(proposal_path)
    proposals = pd.read_csv(proposal_path)
    events = fetch_economic_events_v242(now=now, cfg=cfg) if cfg.get("macro", {}).get("enabled", True) else []
    macro = macro_context_v242(events, now=now, cfg=cfg)
    symbols = set(proposals.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    symbols |= {str(x).upper() for x in cfg.get("news", {}).get("market_context_symbols", [])}
    news_by_symbol: dict[str, dict[str, Any]] = {}
    for symbol in sorted(symbols):
        rows = fetch_eodhd_news_v242(
            symbol, now=now,
            lookback_days=int(cfg["news"].get("lookback_days", 3)),
            limit=int(cfg["news"].get("limit_per_symbol", 30)),
        ) if cfg.get("news", {}).get("enabled", True) else []
        news_by_symbol[symbol] = news_context_v242(symbol, rows, now=now, cfg=cfg)
    contextual = apply_production_context_v242(proposals, macro=macro, news_by_symbol=news_by_symbol, generated_at=now)
    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_42")
    artifact_root.mkdir(parents=True, exist_ok=True)
    contextual.to_csv(artifact_root / "contextual_proposals.csv", index=False)
    snapshot = {
        "schema": "production_intelligence_v2_42",
        "generated_at": now.isoformat(),
        "macro": macro,
        "news": news_by_symbol,
        "proposal_rows": len(contextual),
        "buy_new_rows": int((contextual.get("decision", pd.Series(dtype=str)).astype(str).str.upper() == "BUY_NEW").sum()),
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    (artifact_root / "intelligence_snapshot.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return snapshot
