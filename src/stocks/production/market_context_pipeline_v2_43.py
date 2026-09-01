from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.data.canonical import read_canonical_parquet
from stocks.intelligence_agent.models import NewsArticle
from stocks.intelligence_agent.nlp.engine import FinancialNLP
from stocks.news.evidence import build_news_evidence
from stocks.providers.adapters import (
    alphavantage_news,
    currents_news,
    finnhub_news,
    marketaux_news,
)
from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.providers.yahoo import yahoo_news
from stocks.production.strategy_hydration_v2_42 import selected_forward_symbols_v242

from .reference_macro_v2_43_1 import collect_reference_macro_v2431

from .context_v2_43 import (
    build_snapshot_v243,
    calendar_context_v243,
    causal_news_rows_v243,
    market_data_freshness_v243,
    news_features_v243,
    normalize_economic_event_v243,
    utc,
    verify_snapshot_v243,
)


EODHD_BASE = "https://eodhd.com/api"
FINNHUB_BASE = "https://finnhub.io/api/v1"
_NLP_SINGLETON: FinancialNLP | None = None


def _financial_nlp() -> FinancialNLP:
    global _NLP_SINGLETON
    if _NLP_SINGLETON is None:
        _NLP_SINGLETON = FinancialNLP()
    return _NLP_SINGLETON



def _eodhd_key() -> str:
    return secret("EODHD_API_KEY", "EOD_API_KEY", "EODHISTORICALDATA_API_KEY")


def _provider_state(value: Any) -> str:
    state = getattr(value, "state", None)
    return str(getattr(state, "value", state or "UNKNOWN"))


def _eodhd_economic_raw(
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    key = _eodhd_key()
    if not key:
        return [], "UNCONFIGURED", [{
            "provider": "eodhd",
            "domain": "economic_calendar",
            "configured": False,
            "attempted": False,
            "state": "UNCONFIGURED",
            "retrieved_at": cutoff.isoformat(),
        }]
    calendar = cfg["calendar"]
    start = (cutoff - pd.Timedelta(days=int(calendar.get("lookback_days", 1)))).date().isoformat()
    end = (cutoff + pd.Timedelta(days=int(calendar.get("lookahead_days", 2)))).date().isoformat()
    rows: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    try:
        with ProviderHTTPClient(user_agent="stocks-quant-agent/market-context-v2.43") as client:
            for country in calendar.get("countries", ["US"]):
                data = client.get_json(
                    f"{EODHD_BASE}/economic-events",
                    params={
                        "api_token": key,
                        "fmt": "json",
                        "from": start,
                        "to": end,
                        "country": str(country),
                        "limit": 1000,
                        "offset": 0,
                    },
                )
                if not isinstance(data, list):
                    raise ValueError("EODHD_ECONOMIC_EVENTS_NOT_LIST")
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    row = dict(item)
                    # If EODHD does not provide a release timestamp, the time
                    # at which this live process first observed the payload is
                    # a safe upper bound on information availability. We never
                    # backdate it to scheduled_at.
                    if row.get("actual") not in (None, "") and not any(
                        row.get(key) not in (None, "")
                        for key in (
                            "published_at", "released_at", "release_time",
                            "updated_at", "last_update", "last_updated",
                        )
                    ):
                        row["observed_at"] = cutoff.isoformat()
                    rows.append(row)
        state = "OK" if rows else "EMPTY"
    except Exception as exc:
        state = "ERROR"
        provenance.append({
            "provider": "eodhd",
            "domain": "economic_calendar",
            "state": state,
            "retrieved_at": cutoff.isoformat(),
            "error": f"{type(exc).__name__}:{exc}",
        })
        return [], state, provenance
    provenance.append({
        "provider": "eodhd",
        "domain": "economic_calendar",
        "state": state,
        "retrieved_at": cutoff.isoformat(),
        "rows": len(rows),
    })
    return rows, state, provenance



def _calendar_cache_path(root: Path, cutoff: pd.Timestamp) -> Path:
    return (
        root
        / "artifacts/production_runtime_v2_43_1/calendar_cache"
        / f"economic-calendar-{cutoff.date().isoformat()}.json"
    )


def _finnhub_economic_raw(
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    key = secret("FINNHUB_API_KEY")
    started = time.monotonic()
    if not key:
        return [], "UNCONFIGURED", [{
            "provider": "finnhub",
            "domain": "economic_calendar",
            "configured": False,
            "attempted": False,
            "state": "UNCONFIGURED",
            "retrieved_at": cutoff.isoformat(),
            "elapsed_seconds": 0.0,
        }]
    calendar = cfg["calendar"]
    start = (cutoff - pd.Timedelta(days=int(calendar.get("lookback_days", 1)))).date().isoformat()
    end = (cutoff + pd.Timedelta(days=int(calendar.get("lookahead_days", 2)))).date().isoformat()
    try:
        with ProviderHTTPClient(user_agent="stocks-quant-agent/market-context-v2.43.1") as client:
            data = client.get_json(
                f"{FINNHUB_BASE}/calendar/economic",
                params={"from": start, "to": end, "token": key},
            )
        raw_rows = data.get("economicCalendar", []) if isinstance(data, dict) else []
        if not isinstance(raw_rows, list):
            raise ValueError("FINNHUB_ECONOMIC_CALENDAR_NOT_LIST")
        rows = []
        for item in raw_rows:
            if not isinstance(item, dict):
                continue
            country = str(item.get("country") or "").upper()
            if country and country not in {str(x).upper() for x in calendar.get("countries", ["US"])}:
                continue
            row = dict(item)
            row["event_type"] = row.get("event") or row.get("name") or row.get("type")
            row["forecast"] = row.get("estimate", row.get("forecast"))
            row["previous"] = row.get("prev", row.get("previous"))
            row["scheduled_at"] = row.get("time") or row.get("date")
            row["_provider"] = "finnhub"
            # Historical backfills must never pretend an actual was visible at
            # scheduled time. Live first-observation time is safe.
            if row.get("actual") not in (None, "") and not any(
                row.get(k) not in (None, "")
                for k in ("published_at", "released_at", "release_time", "updated_at")
            ):
                row["observed_at"] = cutoff.isoformat()
            rows.append(row)
        state = "OK" if rows else "EMPTY"
        return rows, state, [{
            "provider": "finnhub",
            "domain": "economic_calendar",
            "configured": True,
            "attempted": True,
            "state": state,
            "retrieved_at": cutoff.isoformat(),
            "rows": len(rows),
            "elapsed_seconds": round(time.monotonic() - started, 4),
        }]
    except Exception as exc:
        return [], "ERROR", [{
            "provider": "finnhub",
            "domain": "economic_calendar",
            "configured": True,
            "attempted": True,
            "state": "ERROR",
            "retrieved_at": cutoff.isoformat(),
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            "elapsed_seconds": round(time.monotonic() - started, 4),
        }]


def _dedupe_calendar_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        event = str(row.get("event_type") or row.get("event") or row.get("name") or row.get("type") or "UNKNOWN").strip().lower()
        country = str(row.get("country") or row.get("country_code") or "").upper()
        raw_time = row.get("scheduled_at") or row.get("event_time") or row.get("time") or row.get("date")
        try:
            stamp = utc(raw_time).floor("min").isoformat()
        except Exception:
            continue
        key = (country, event, stamp)
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def collect_economic_calendar_v2431(
    root: Path,
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    providers = [str(x).lower() for x in cfg["calendar"].get("providers", ["eodhd", "finnhub"])]
    all_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    usable = False
    for provider in providers:
        if provider == "eodhd":
            rows, state, diag = _eodhd_economic_raw(cutoff=cutoff, cfg=cfg)
            for row in rows:
                row["_provider"] = "eodhd"
        elif provider == "finnhub":
            rows, state, diag = _finnhub_economic_raw(cutoff=cutoff, cfg=cfg)
        else:
            rows, state, diag = [], "UNSUPPORTED", [{
                "provider": provider,
                "domain": "economic_calendar",
                "configured": False,
                "attempted": False,
                "state": "UNSUPPORTED",
                "retrieved_at": cutoff.isoformat(),
            }]
        diagnostics.extend(diag)
        all_rows.extend(rows)
        usable = usable or state in {"OK", "EMPTY"}

    cache_path = _calendar_cache_path(root, cutoff)
    cache_ttl = float(cfg["calendar"].get("cache_ttl_hours", 6.0))
    if usable:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({
            "retrieved_at": cutoff.isoformat(),
            "rows": all_rows,
            "providers": diagnostics,
        }, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return _dedupe_calendar_rows(all_rows), "OK" if all_rows else "EMPTY", diagnostics

    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            stamp = utc(cached["retrieved_at"])
            age = (cutoff - stamp).total_seconds() / 3600.0
            if 0 <= age <= cache_ttl:
                diagnostics.append({
                    "provider": "cache",
                    "domain": "economic_calendar",
                    "state": "CACHED_OK",
                    "retrieved_at": cutoff.isoformat(),
                    "cache_age_hours": age,
                    "rows": len(cached.get("rows") or []),
                })
                return _dedupe_calendar_rows(list(cached.get("rows") or [])), "OK", diagnostics
        except Exception as exc:
            diagnostics.append({
                "provider": "cache",
                "domain": "economic_calendar",
                "state": "ERROR",
                "retrieved_at": cutoff.isoformat(),
                "error_type": type(exc).__name__,
            })
    return [], "ERROR", diagnostics

def _eodhd_news_raw(
    symbol: str,
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    key = _eodhd_key()
    if not key:
        return [], "UNCONFIGURED"
    news = cfg["news"]
    start = (cutoff - pd.Timedelta(hours=int(news.get("lookback_hours", 72)))).date().isoformat()
    end = cutoff.date().isoformat()
    try:
        with ProviderHTTPClient(user_agent="stocks-quant-agent/market-context-v2.43") as client:
            data = client.get_json(
                f"{EODHD_BASE}/news",
                params={
                    "api_token": key,
                    "fmt": "json",
                    "s": f"{symbol.upper()}.US",
                    "from": start,
                    "to": end,
                    "limit": int(news.get("limit_per_symbol", 40)),
                    "offset": 0,
                },
            )
        if not isinstance(data, list):
            raise ValueError("EODHD_NEWS_NOT_LIST")
        rows = []
        for raw in data:
            if not isinstance(raw, dict) or not raw.get("title") or not raw.get("date"):
                continue
            link = str(raw.get("link") or "")
            rows.append({
                "provider": "eodhd",
                "provider_id": str(raw.get("id") or f"{symbol}:{raw.get('date')}:{raw.get('title')}"),
                "published_at": utc(raw["date"]).isoformat(),
                "title": str(raw["title"]),
                "url": link,
                "summary": str(raw.get("content") or "")[:4000],
                "source_name": link.split("/")[2] if link.startswith("http") and len(link.split("/")) > 2 else "",
                "symbols": [symbol.upper()],
                "categories": list(raw.get("tags") or []),
                "provider_sentiment": (
                    (raw.get("sentiment") or {}).get("polarity")
                    if isinstance(raw.get("sentiment"), dict)
                    else None
                ),
                "metadata": {"provider_payload_type": "eodhd_news"},
            })
        return rows, "OK" if rows else "EMPTY"
    except Exception:
        return [], "ERROR"


def _collect_news(
    symbol: str,
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    configured = {str(x).lower() for x in cfg["news"].get("providers", [])}
    rows: list[dict[str, Any]] = []
    states: dict[str, str] = {}
    provenance: list[dict[str, Any]] = []

    if "eodhd" in configured:
        part, state = _eodhd_news_raw(symbol, cutoff=cutoff, cfg=cfg)
        rows.extend(part)
        states["eodhd"] = state

    if "yfinance" in configured:
        try:
            part = [item.to_dict() for item in yahoo_news(symbol)]
            rows.extend(part)
            states["yfinance"] = "OK" if part else "EMPTY"
        except Exception:
            states["yfinance"] = "ERROR"

    adapters = {
        "finnhub": finnhub_news,
        "alphavantage": alphavantage_news,
        "marketaux": marketaux_news,
        "currents": currents_news,
    }
    for name, adapter in adapters.items():
        if name not in configured:
            continue
        try:
            result = adapter(symbol)
            states[name] = _provider_state(result)
            rows.extend(list(getattr(result, "items", []) or []))
        except Exception:
            states[name] = "ERROR"

    causal = causal_news_rows_v243(rows, decision_cutoff=cutoff)
    for provider, state in sorted(states.items()):
        provenance.append({
            "provider": provider,
            "domain": "news",
            "symbol": symbol.upper(),
            "state": state,
            "retrieved_at": cutoff.isoformat(),
        })
    return causal, states, provenance


def _classify_stories(
    symbol: str,
    rows: list[dict[str, Any]],
    *,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    if not rows:
        return [], True
    evidence = build_news_evidence(
        rows,
        target_symbol=symbol,
        now=cutoff.to_pydatetime(),
    )
    threshold = float(cfg["news"].get("minimum_story_evidence_score", 0.12))
    selected = [item for item in evidence if float(item.evidence_score) >= threshold]
    nlp = _financial_nlp()
    stories = []
    finbert_ready = True
    for item in selected:
        article = NewsArticle(
            article_id=item.story_id,
            published_at=item.published_at,
            title=item.title,
            body=item.summary,
            source="|".join(item.providers),
            url=item.urls[0] if item.urls else "",
            symbols=(symbol.upper(),),
        )
        try:
            signals = nlp.classify_article(
                article,
                now=cutoff.to_pydatetime(),
                source_quality=float(item.source_quality),
            )
            signal = signals[0] if signals else None
        except Exception:
            signal = None
            finbert_ready = False
        stories.append({
            **item.to_dict(),
            "sentiment": (
                float(signal.sentiment) if signal is not None else float(item.sentiment)
            ),
            "event_type": (
                str(signal.event_type.value)
                if signal is not None
                else str(item.event_type or "unclassified").lower()
            ),
            "event_severity": (
                float(signal.event_severity)
                if signal is not None
                else float(item.event_severity or 0.0)
            ),
        })
    return stories, finbert_ready


def _market_regime(
    frames: dict[str, pd.DataFrame],
    *,
    cutoff: pd.Timestamp,
) -> dict[str, Any]:
    def ret(symbol: str, bars: int) -> float | None:
        frame = frames.get(symbol)
        if frame is None or frame.empty:
            return None
        close = pd.to_numeric(frame["close"], errors="coerce").dropna()
        if len(close) <= bars:
            return None
        return float(close.iloc[-1] / close.iloc[-bars - 1] - 1.0)

    spy20 = ret("SPY", 20)
    qqq20 = ret("QQQ", 20)
    values = [x for x in (spy20, qqq20) if x is not None]
    score = float(sum(values) / len(values)) if values else 0.0
    regime = "UNKNOWN"
    if values:
        regime = "RISK_ON" if score >= 0.02 else "RISK_OFF" if score <= -0.02 else "NEUTRAL"
    return {
        "label": regime,
        "score": score,
        "spy_return_20h": spy20,
        "qqq_return_20h": qqq20,
        "as_of": cutoff.isoformat(),
        "authority": "CONTEXT_ONLY",
    }


def _snapshot_paths(root: Path, cfg: dict[str, Any], snapshot_id: str) -> tuple[Path, Path]:
    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_43")
    return (
        artifact_root / "snapshots" / f"{snapshot_id}.json",
        artifact_root / "latest_snapshot_pointer.json",
    )


def write_snapshot_v243(
    root: Path,
    cfg: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    if not verify_snapshot_v243(snapshot):
        raise ValueError("MARKET_CONTEXT_SNAPSHOT_HASH_INVALID")
    immutable, pointer = _snapshot_paths(root, cfg, snapshot["snapshot_id"])
    immutable.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(snapshot, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if immutable.exists():
        existing = json.loads(immutable.read_text(encoding="utf-8"))
        if existing != snapshot:
            raise RuntimeError("IMMUTABLE_SNAPSHOT_ID_COLLISION")
    else:
        immutable.write_text(encoded, encoding="utf-8")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(
        json.dumps({
            "schema": "market_context_pointer_v2_43",
            "snapshot_id": snapshot["snapshot_id"],
            "decision_cutoff": snapshot["decision_cutoff"],
            "path": str(immutable.relative_to(root)),
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"snapshot_path": str(immutable), "pointer_path": str(pointer)}


def build_market_context_snapshot_v243(
    root: str | Path,
    production_cfg: dict[str, Any],
    cfg: dict[str, Any],
    *,
    decision_cutoff: Any | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    load_project_env(root)
    cutoff = utc(decision_cutoff if decision_cutoff is not None else pd.Timestamp.now(tz="UTC"))
    provider_root = root / production_cfg["data"]["provider_root"]
    symbols = set(str(x).upper() for x in production_cfg["data"].get("symbols", []))
    symbols.update(selected_forward_symbols_v242(root, maximum_symbols=50))
    symbols.update(str(x).upper() for x in cfg["news"].get("market_context_symbols", []))
    symbols = sorted(symbols)

    frames: dict[str, pd.DataFrame] = {}
    freshness: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for symbol in symbols:
        path = provider_root / f"{symbol}_{production_cfg['data']['timeframe']}.parquet"
        if not path.is_file():
            freshness.append({"symbol": symbol, "status": "MISSING", "provider": "EODHD+IBKR"})
            continue
        frame, meta = read_canonical_parquet(path, verify_hash=False, verify_metadata=False)
        frames[symbol] = frame
        source = str((meta or {}).get("source") or "CANONICAL")
        freshness.append(
            market_data_freshness_v243(
                symbol,
                frame,
                decision_cutoff=cutoff,
                cfg=cfg,
                provider=source,
            )
        )
        provenance.append({
            "provider": source,
            "domain": "market_data",
            "symbol": symbol,
            "canonical_path": str(path),
            "retrieved_at": cutoff.isoformat(),
        })

    raw_events, calendar_state, calendar_prov = collect_economic_calendar_v2431(
        root, cutoff=cutoff, cfg=cfg
    )
    provenance.extend(calendar_prov)
    normalized_events = []
    for raw in raw_events:
        try:
            normalized_events.append(
                normalize_economic_event_v243(
                    raw,
                    decision_cutoff=cutoff,
                    provider=str(raw.get("_provider") or "economic_calendar"),
                    cfg=cfg,
                )
            )
        except Exception as exc:
            provenance.append({
                "provider": str(raw.get("_provider") or "economic_calendar"),
                "domain": "economic_calendar_normalization",
                "state": "ERROR",
                "retrieved_at": cutoff.isoformat(),
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:500],
            })
            continue
    calendar = calendar_context_v243(
        normalized_events,
        decision_cutoff=cutoff,
        data_freshness=freshness,
        source_status=calendar_state,
        retrieved_at=cutoff,
        cfg=cfg,
    )
    calendar["provider_diagnostics"] = calendar_prov
    calendar["provider_count"] = len({str(row.get("provider")) for row in calendar_prov})

    news_context: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        rows, states, news_prov = _collect_news(symbol, cutoff=cutoff, cfg=cfg)
        provenance.extend(news_prov)
        stories, finbert_ready = _classify_stories(symbol, rows, cutoff=cutoff, cfg=cfg)
        features = news_features_v243(
            stories,
            decision_cutoff=cutoff,
            provider_states=states,
        )
        news_context[symbol] = {
            **features,
            "news_present": bool(stories),
            "finbert_ready": bool(finbert_ready),
            "stories": stories[:12],
        }

    regime = _market_regime(frames, cutoff=cutoff)
    reference_macro = collect_reference_macro_v2431(
        root,
        cutoff=cutoff,
        ttl_hours=float(cfg.get("reference_macro", {}).get("cache_ttl_hours", 6.0)),
        lookback_days=int(cfg.get("reference_macro", {}).get("lookback_days", 450)),
    ) if bool(cfg.get("reference_macro", {}).get("enabled", True)) else {"status": "DISABLED"}
    regime["reference_macro"] = reference_macro
    provenance.append({
        "provider": "references/Stocks.macro",
        "domain": "macro_regime",
        "state": str(reference_macro.get("status") or "UNKNOWN"),
        "retrieved_at": cutoff.isoformat(),
        "execution_authority": "NONE",
    })

    snapshot = build_snapshot_v243(
        decision_cutoff=cutoff,
        symbols=symbols,
        market_regime=regime,
        calendar_context=calendar,
        news_context=news_context,
        data_freshness=freshness,
        provider_provenance=provenance,
    ).to_dict()
    paths = write_snapshot_v243(root, cfg, snapshot)
    return {
        "schema": "market_context_build_v2_43",
        "status": "SUCCEEDED",
        "snapshot_id": snapshot["snapshot_id"],
        "decision_cutoff": snapshot["decision_cutoff"],
        "calendar_status": calendar["status"],
        "calendar_entry_blockers": calendar["entry_blockers"],
        "calendar_provider_diagnostics": calendar_prov,
        "reference_macro_status": reference_macro.get("status"),
        "symbols": symbols,
        "fresh_market_symbols": sum(row.get("status") == "FRESH" for row in freshness),
        "total_market_symbols": len(freshness),
        "paths": paths,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def load_latest_snapshot_v243(root: str | Path, cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    artifact_root = root / cfg.get("artifact_root", "artifacts/production_runtime_v2_43")
    pointer = artifact_root / "latest_snapshot_pointer.json"
    if not pointer.is_file():
        raise FileNotFoundError(pointer)
    meta = json.loads(pointer.read_text(encoding="utf-8"))
    path = root / str(meta["path"])
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if str(snapshot.get("snapshot_id")) != str(meta.get("snapshot_id")):
        raise ValueError("MARKET_CONTEXT_POINTER_ID_MISMATCH")
    if not verify_snapshot_v243(snapshot):
        raise ValueError("MARKET_CONTEXT_SNAPSHOT_HASH_INVALID")
    return snapshot


__all__ = [
    "build_market_context_snapshot_v243",
    "collect_economic_calendar_v2431",
    "load_latest_snapshot_v243",
    "write_snapshot_v243",
]
