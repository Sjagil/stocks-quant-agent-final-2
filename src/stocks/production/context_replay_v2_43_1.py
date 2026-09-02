from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.orchestration.strategy_forward_signals import evaluate_latest_entry_condition
from stocks.providers.env import load_project_env
from stocks.providers.http import ProviderHTTPClient

from .context_v2_43 import (
    apply_context_policy_v243,
    build_snapshot_v243,
    calendar_context_v243,
    market_data_freshness_v243,
    news_features_v243,
    normalize_economic_event_v243,
)
from .market_context_pipeline_v2_43 import (
    EODHD_BASE,
    _classify_stories,
    _eodhd_key,
    _market_regime,
)


def _utc(value: Any) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _params(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("params_json", "{}")
    return dict(raw) if isinstance(raw, dict) else dict(json.loads(str(raw)))


def _market_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "timestamp" in frame.columns:
        frame = frame.set_index("timestamp")
    elif "date" in frame.columns:
        frame = frame.set_index("date")
    frame.index = pd.to_datetime(frame.index, utc=True)
    frame = frame.sort_index(kind="stable")
    # Strategy adapters expect a date column in the canonical prepared shape.
    if "date" not in frame.columns:
        frame = frame.copy()
        frame["date"] = frame.index
    return frame


def _load_local_news(root: Path) -> list[dict[str, Any]]:
    candidates = [
        root / "data/nlp/financial_news.jsonl",
        root / "data/news/financial_news.jsonl",
        root / "data/news/ibkr/private/headlines.jsonl",
    ]
    rows: list[dict[str, Any]] = []
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            published = row.get("published_at") or row.get("date") or row.get("datetime")
            title = row.get("title") or row.get("headline")
            if not published or not title:
                continue
            try:
                stamp = _utc(published)
            except Exception:
                continue
            rows.append({
                "provider": str(row.get("provider") or row.get("source") or "local_archive"),
                "provider_id": str(row.get("provider_id") or row.get("article_id") or ""),
                "published_at": stamp.isoformat(),
                "title": str(title),
                "summary": str(row.get("summary") or row.get("body") or row.get("content") or "")[:4000],
                "url": str(row.get("url") or row.get("link") or ""),
                "source_name": str(row.get("source_name") or row.get("source") or "local_archive"),
                "symbols": list(row.get("symbols") or ([row.get("symbol")] if row.get("symbol") else [])),
                "categories": list(row.get("categories") or []),
                "metadata": {"replay_source": str(path)},
            })
    return rows


def _fetch_eodhd_news_history(
    root: Path,
    symbol: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    maximum_rows: int = 1000,
) -> tuple[list[dict[str, Any]], str]:
    key = _eodhd_key()
    cache = root / "artifacts/research_runtime/context_historical_replay_v2_43_1/cache" / f"news-{symbol}-{start.date()}-{end.date()}.json"
    if cache.is_file():
        try:
            return list(json.loads(cache.read_text(encoding="utf-8")).get("rows") or []), "CACHE"
        except Exception:
            pass
    if not key:
        return [], "UNCONFIGURED"
    try:
        with ProviderHTTPClient(user_agent="stocks-quant-agent/context-replay-v2.43.1") as client:
            data = client.get_json(
                f"{EODHD_BASE}/news",
                params={
                    "api_token": key,
                    "fmt": "json",
                    "s": f"{symbol}.US",
                    "from": start.date().isoformat(),
                    "to": end.date().isoformat(),
                    "limit": int(maximum_rows),
                    "offset": 0,
                },
            )
        if not isinstance(data, list):
            raise ValueError("EODHD_NEWS_HISTORY_NOT_LIST")
        rows = []
        for raw in data:
            if not isinstance(raw, dict) or not raw.get("title") or not raw.get("date"):
                continue
            rows.append({
                "provider": "eodhd_replay",
                "provider_id": str(raw.get("id") or ""),
                "published_at": _utc(raw["date"]).isoformat(),
                "title": str(raw["title"]),
                "url": str(raw.get("link") or ""),
                "summary": str(raw.get("content") or "")[:4000],
                "source_name": str(raw.get("link") or "").split("/")[2] if str(raw.get("link") or "").startswith("http") else "",
                "symbols": [symbol],
                "categories": list(raw.get("tags") or []),
                "metadata": {"replay_source": "EODHD_HISTORICAL_QUERY"},
            })
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"rows": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return rows, "OK" if rows else "EMPTY"
    except Exception as exc:
        return [], f"ERROR:{type(exc).__name__}"


def _fetch_eodhd_calendar_history(
    root: Path,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    key = _eodhd_key()
    cache = root / "artifacts/research_runtime/context_historical_replay_v2_43_1/cache" / f"calendar-{start.date()}-{end.date()}.json"
    if cache.is_file():
        try:
            return list(json.loads(cache.read_text(encoding="utf-8")).get("rows") or []), "CACHE"
        except Exception:
            pass
    if not key:
        return [], "UNCONFIGURED"
    rows: list[dict[str, Any]] = []
    try:
        with ProviderHTTPClient(user_agent="stocks-quant-agent/context-replay-v2.43.1") as client:
            for country in cfg["calendar"].get("countries", ["US"]):
                data = client.get_json(
                    f"{EODHD_BASE}/economic-events",
                    params={
                        "api_token": key,
                        "fmt": "json",
                        "from": start.date().isoformat(),
                        "to": end.date().isoformat(),
                        "country": str(country),
                        "limit": 1000,
                        "offset": 0,
                    },
                )
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            row = dict(item)
                            # Never backdate an actual whose release timestamp was not archived.
                            if not any(row.get(k) not in (None, "") for k in (
                                "published_at", "released_at", "release_time", "updated_at", "last_update", "last_updated"
                            )):
                                row.pop("actual", None)
                                row.pop("revision", None)
                            rows.append(row)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"rows": rows}, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return rows, "OK" if rows else "EMPTY"
    except Exception as exc:
        return [], f"ERROR:{type(exc).__name__}"


def _symbol_news(
    symbol: str,
    all_rows: list[dict[str, Any]],
    *,
    cutoff: pd.Timestamp,
    lookback_hours: int,
) -> list[dict[str, Any]]:
    lower = cutoff - pd.Timedelta(hours=int(lookback_hours))
    out = []
    for row in all_rows:
        try:
            stamp = _utc(row.get("published_at"))
        except Exception:
            continue
        if not (lower <= stamp <= cutoff):
            continue
        symbols = {str(x).upper() for x in row.get("symbols", []) if x}
        title = str(row.get("title") or "").upper()
        if symbol not in symbols and symbol not in title:
            continue
        out.append(row)
    return out


def historical_context_replay_v2431(
    root: str | Path,
    production_cfg: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Generate historical context-on/off evidence without future information.

    Strategy signals are recomputed on a frame truncated at each cutoff. News is
    filtered by published_at <= cutoff. Economic actual/revision values without a
    verifiable release timestamp are removed from historical backfills.
    """
    root = Path(root).resolve()
    load_project_env(root)
    out_root = root / "artifacts/research_runtime/context_historical_replay_v2_43_1"
    out_root.mkdir(parents=True, exist_ok=True)

    matrix_path = root / "artifacts/research_runtime/candidate_strategy_matrix/matrix.csv"
    roster_path = root / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    if not matrix_path.is_file() or not roster_path.is_file():
        report = {"schema": "context_historical_replay_v2_43_1", "status": "MISSING_STRATEGY_INPUTS", "observations": 0, "leakage_safe": True, "execution_authority": "NONE"}
        (out_root / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return report

    matrix = pd.read_csv(matrix_path)
    roster = pd.read_csv(roster_path)
    if matrix.empty or roster.empty:
        return {"schema": "context_historical_replay_v2_43_1", "status": "EMPTY_STRATEGY_INPUTS", "observations": 0, "leakage_safe": True, "execution_authority": "NONE"}

    status_col = "roster_status" if "roster_status" in roster.columns else None
    if status_col:
        roster = roster.loc[roster[status_col].astype(str).eq("BROADLY_VALIDATED_FINALIST")]
    roster_map = {str(row["hypothesis_id"]): row for row in roster.to_dict(orient="records") if row.get("hypothesis_id")}

    provider_root = root / production_cfg["data"]["provider_root"]
    horizon = int(cfg["walk_forward"].get("horizon_bars", 20))
    max_samples = int(cfg["walk_forward"].get("maximum_samples", 160))
    stride = max(1, int(cfg["walk_forward"].get("sample_stride_bars", 6)))
    lookback_days = int(cfg["walk_forward"].get("historical_lookback_days", 180))
    now = pd.Timestamp.now(tz="UTC")
    start = now - pd.Timedelta(days=lookback_days)

    local_news = _load_local_news(root)
    calendar_rows, calendar_provider_state = _fetch_eodhd_calendar_history(
        root, start=start - pd.Timedelta(days=2), end=now + pd.Timedelta(days=2), cfg=cfg
    )

    candidates = []
    for row in matrix.to_dict(orient="records"):
        hypothesis_id = str(row.get("hypothesis_id") or "")
        if hypothesis_id not in roster_map:
            continue
        if not _truthy(row.get("local_evidence_positive", False)):
            continue
        symbol = str(row.get("symbol") or "").upper()
        path = provider_root / f"{symbol}_{production_cfg['data']['timeframe']}.parquet"
        if not path.is_file():
            continue
        candidates.append((row, roster_map[hypothesis_id], path))

    rows_out: list[dict[str, Any]] = []
    news_cache: dict[str, tuple[list[dict[str, Any]], str]] = {}
    price_cache: dict[str, pd.DataFrame] = {}
    benchmark_frames: dict[str, pd.DataFrame] = {}
    for benchmark in ("SPY", "QQQ"):
        path = provider_root / f"{benchmark}_{production_cfg['data']['timeframe']}.parquet"
        if path.is_file():
            benchmark_frames[benchmark] = _market_frame(path)

    for matrix_row, roster_row, path in candidates:
        if len(rows_out) >= max_samples:
            break
        symbol = str(matrix_row["symbol"]).upper()
        market = price_cache.setdefault(symbol, _market_frame(path))
        eligible_index = market.index[(market.index >= start) & (market.index < now)]
        if len(eligible_index) < horizon + 60:
            continue
        if symbol not in news_cache:
            fetched, state = _fetch_eodhd_news_history(root, symbol, start=start - pd.Timedelta(days=4), end=now)
            merged = [*local_news, *fetched]
            news_cache[symbol] = (merged, state if state not in {"UNCONFIGURED"} else ("OK" if local_news else state))
        all_news, news_state = news_cache[symbol]

        # Walk backwards so the most recent causal samples are evaluated first.
        for cutoff in list(eligible_index[:-horizon:stride])[::-1]:
            if len(rows_out) >= max_samples:
                break
            prior = market.loc[market.index <= cutoff]
            future = market.loc[market.index > cutoff]
            if len(prior) < 60 or len(future) < horizon:
                continue
            try:
                signal = evaluate_latest_entry_condition(
                    strategy=str(matrix_row["strategy"]),
                    frame=prior,
                    params=_params(roster_row),
                )
            except Exception:
                continue
            if not bool(signal.get("ready")):
                continue

            cutoff_ts = _utc(cutoff)
            # Replay only scheduled future events. Backfilled actual availability
            # cannot be proven unless a provider release timestamp is present.
            normalized = []
            for raw in calendar_rows:
                try:
                    event = normalize_economic_event_v243(
                        raw,
                        decision_cutoff=cutoff_ts,
                        provider="eodhd_replay",
                        cfg=cfg,
                    )
                    if _utc(event.scheduled_at) >= cutoff_ts:
                        normalized.append(event)
                except Exception:
                    continue

            freshness = []
            regime_frames = {symbol: prior}
            for bench, bench_frame in benchmark_frames.items():
                bench_prior = bench_frame.loc[bench_frame.index <= cutoff_ts]
                regime_frames[bench] = bench_prior
                freshness.append(market_data_freshness_v243(
                    bench, bench_prior, decision_cutoff=cutoff_ts, cfg=cfg, provider="HISTORICAL_CANONICAL_REPLAY"
                ))
            if symbol not in {"SPY", "QQQ"}:
                freshness.append(market_data_freshness_v243(
                    symbol, prior, decision_cutoff=cutoff_ts, cfg=cfg, provider="HISTORICAL_CANONICAL_REPLAY"
                ))
            calendar = calendar_context_v243(
                normalized,
                decision_cutoff=cutoff_ts,
                data_freshness=freshness,
                source_status=("OK" if calendar_provider_state in {"OK", "EMPTY", "CACHE"} else "ERROR"),
                retrieved_at=cutoff_ts,
                cfg=cfg,
            )

            causal_news = _symbol_news(
                symbol, all_news, cutoff=cutoff_ts, lookback_hours=int(cfg["news"].get("lookback_hours", 72))
            )
            stories, finbert_ready = _classify_stories(symbol, causal_news, cutoff=cutoff_ts, cfg=cfg)
            features = news_features_v243(
                stories,
                decision_cutoff=cutoff_ts,
                provider_states={"eodhd_replay": ("OK" if news_state in {"OK", "EMPTY", "CACHE"} else news_state)},
            )
            news_context = {
                symbol: {**features, "news_present": bool(stories), "finbert_ready": bool(finbert_ready), "stories": stories[:12]}
            }
            snapshot = build_snapshot_v243(
                decision_cutoff=cutoff_ts,
                symbols=[symbol, "SPY", "QQQ"],
                market_regime=_market_regime(regime_frames, cutoff=cutoff_ts),
                calendar_context=calendar,
                news_context=news_context,
                data_freshness=freshness,
                provider_provenance=[
                    {"provider": "historical_replay", "domain": "market_data", "retrieved_at": cutoff_ts.isoformat()},
                    {"provider": "eodhd_replay", "domain": "economic_calendar", "state": calendar_provider_state, "retrieved_at": cutoff_ts.isoformat()},
                    {"provider": "eodhd_replay/local_archive", "domain": "news", "state": news_state, "retrieved_at": cutoff_ts.isoformat()},
                ],
            ).to_dict()
            conviction = max(0.65, min(0.95, float(matrix_row.get("applicability_score") or 70.0) / 100.0))
            raw = pd.DataFrame([{
                "symbol": symbol,
                "decision": "BUY_NEW",
                "conviction": conviction,
                "blockers": "",
                "fresh_entry_trigger": True,
                "shariah_verified": True,
            }])
            contextual = apply_context_policy_v243(raw, snapshot=snapshot, cfg=cfg, agent_shadow=None, now=cutoff_ts)
            after = str(contextual.iloc[0]["decision_after_context"])
            p0 = float(prior["close"].iloc[-1])
            p1 = float(future["close"].iloc[horizon - 1])
            rows_out.append({
                "symbol": symbol,
                "hypothesis_id": str(matrix_row.get("hypothesis_id")),
                "strategy": str(matrix_row.get("strategy")),
                "cutoff": cutoff_ts.isoformat(),
                "signal_reason": signal.get("reason"),
                "forward_return": p1 / p0 - 1.0,
                "context_off_active": True,
                "context_on_active": after == "BUY_NEW",
                "decision_after_context": after,
                "calendar_adjustment": float(contextual.iloc[0]["calendar_adjustment"]),
                "news_adjustment": float(contextual.iloc[0]["news_adjustment"]),
                "context_blockers": str(contextual.iloc[0]["context_blockers"]),
                "news_story_count": int(features.get("story_count", 0)),
                "calendar_provider_state": calendar_provider_state,
                "news_provider_state": news_state,
            })

    frame = pd.DataFrame(rows_out)
    if not frame.empty:
        frame.to_csv(out_root / "observations.csv", index=False)
    minimum = int(cfg["walk_forward"].get("minimum_observations", 20))
    minimum_off = int(cfg["walk_forward"].get("minimum_context_off_active", 5))
    minimum_on = int(cfg["walk_forward"].get("minimum_context_on_active", 5))

    off = frame.loc[frame["context_off_active"] == True] if not frame.empty else frame  # noqa: E712
    on = frame.loc[frame["context_on_active"] == True] if not frame.empty else frame  # noqa: E712

    status = (
        "PASSED"
        if (
            len(frame) >= minimum
            and len(off) >= minimum_off
            and len(on) >= minimum_on
        )
        else "INSUFFICIENT_CONTEXT_HISTORY"
    )
    report = {
        "schema": "context_historical_replay_v2_43_1",
        "status": status,
        "leakage_safe": True,
        "causal_strategy_recomputed_at_cutoff": True,
        "future_news_excluded": True,
        "unverifiable_historical_economic_actuals_removed": True,
        "post_release_actual_visibility_backfill_assumed": False,
        "horizon_bars": horizon,
        "observations": len(frame),
        "minimum_observations": minimum,
        "context_off_active": len(off),
        "context_on_active": len(on),
        "context_off_mean_forward_return": float(off["forward_return"].mean()) if len(off) else None,
        "context_on_mean_forward_return": float(on["forward_return"].mean()) if len(on) else None,
        "calendar_provider_state": calendar_provider_state,
        "symbols_with_news_cache": len(news_cache),
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    (out_root / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return report


__all__ = ["historical_context_replay_v2431"]
