from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal


SCHEMA = "market_context_v2_43"


def utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    )


def _hash(payload: Any) -> str:
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _number(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _impact(event_type: str, cfg: dict[str, Any]) -> str:
    text = f" {str(event_type).lower()} "
    calendar = cfg["calendar"]
    if any(str(term).lower() in text for term in calendar.get("high_impact_keywords", [])):
        return "HIGH"
    if any(str(term).lower() in text for term in calendar.get("medium_impact_keywords", [])):
        return "MEDIUM"
    return "LOW"


def _affected_exposures(event_type: str, country: str, currency: str) -> tuple[str, ...]:
    text = str(event_type).lower()
    out = {currency.upper()} if currency else set()
    if str(country).upper() in {"US", "USA", "UNITED STATES"}:
        out.update({"SPY", "QQQ", "US_RATES", "USD"})
    if any(k in text for k in ("oil", "opec", "crude")):
        out.update({"OIL", "ENERGY"})
    if any(k in text for k in ("gold", "inflation", "rate", "fomc", "fed")):
        out.add("GLD")
    return tuple(sorted(x for x in out if x))


@dataclass(frozen=True)
class EconomicEventV243:
    event_id: str
    event_type: str
    country: str
    currency: str
    scheduled_at: str
    published_at: str | None
    impact: str
    forecast: float | None
    previous: float | None
    actual: float | None
    revision: float | None
    surprise: float | None
    affected_exposures: tuple[str, ...]
    provider: str
    release_visibility: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["affected_exposures"] = list(self.affected_exposures)
        return payload


def normalize_economic_event_v243(
    raw: dict[str, Any],
    *,
    decision_cutoff: Any,
    provider: str = "eodhd",
    cfg: dict[str, Any],
) -> EconomicEventV243:
    cutoff = utc(decision_cutoff)
    scheduled_raw = raw.get("scheduled_at") or raw.get("event_time") or raw.get("date")
    if not scheduled_raw:
        raise ValueError("ECONOMIC_EVENT_SCHEDULE_MISSING")
    scheduled = utc(scheduled_raw)

    published_raw = None
    for key in (
        "published_at", "released_at", "release_time",
        "updated_at", "last_update", "last_updated", "observed_at",
    ):
        if raw.get(key) not in (None, ""):
            published_raw = raw[key]
            break
    published = utc(published_raw) if published_raw is not None else None

    event_type = str(
        raw.get("event_type")
        or raw.get("type")
        or raw.get("event")
        or raw.get("name")
        or "UNKNOWN"
    ).strip()
    country = str(raw.get("country") or raw.get("country_code") or "").upper()
    currency = str(raw.get("currency") or ("USD" if country in {"US", "USA"} else "")).upper()
    impact = str(raw.get("impact") or raw.get("importance") or "").upper()
    if impact not in {"HIGH", "MEDIUM", "LOW"}:
        impact = _impact(event_type, cfg)

    forecast = _number(raw.get("forecast"))
    previous = _number(raw.get("previous"))
    raw_actual = _number(raw.get("actual"))
    raw_revision = _number(raw.get("revision"))

    visible_release = published is not None and published <= cutoff and scheduled <= cutoff
    actual = raw_actual if visible_release else None
    revision = raw_revision if visible_release else None
    surprise = (
        actual - forecast
        if visible_release and actual is not None and forecast is not None
        else None
    )
    visibility = (
        "VISIBLE"
        if visible_release
        else "FUTURE_RELEASE"
        if published is not None and published > cutoff
        else "UNVERIFIED_RELEASE_TIME"
        if raw_actual is not None and published is None
        else "SCHEDULE_ONLY"
    )

    identity = str(raw.get("event_id") or raw.get("id") or "").strip()
    if not identity:
        identity = _hash({
            "provider": provider,
            "event_type": event_type,
            "country": country,
            "scheduled_at": scheduled.isoformat(),
        })[:24]

    return EconomicEventV243(
        event_id=identity,
        event_type=event_type,
        country=country,
        currency=currency,
        scheduled_at=scheduled.isoformat(),
        published_at=published.isoformat() if published is not None else None,
        impact=impact,
        forecast=forecast,
        previous=previous,
        actual=actual,
        revision=revision,
        surprise=surprise,
        affected_exposures=_affected_exposures(event_type, country, currency),
        provider=str(provider),
        release_visibility=visibility,
    )


def causal_news_rows_v243(
    rows: Iterable[dict[str, Any]],
    *,
    decision_cutoff: Any,
) -> list[dict[str, Any]]:
    cutoff = utc(decision_cutoff)
    output: list[dict[str, Any]] = []
    for raw in rows:
        value = raw.get("published_at")
        if not value:
            continue
        try:
            published = utc(value)
        except Exception:
            continue
        if published > cutoff:
            continue
        row = dict(raw)
        row["published_at"] = published.isoformat()
        output.append(row)
    return sorted(output, key=lambda row: row["published_at"])


def news_features_v243(
    stories: Iterable[dict[str, Any]],
    *,
    decision_cutoff: Any,
    provider_states: dict[str, str] | None = None,
) -> dict[str, Any]:
    cutoff = utc(decision_cutoff)
    rows = []
    for raw in stories:
        try:
            published = utc(raw["published_at"])
        except Exception:
            continue
        if published > cutoff:
            continue
        row = dict(raw)
        row["_published"] = published
        row["_sentiment"] = float(raw.get("sentiment") or 0.0)
        row["_weight"] = max(float(raw.get("evidence_score") or 0.0), 1e-9)
        row["_severity"] = max(0.0, min(1.0, float(raw.get("event_severity") or 0.0)))
        rows.append(row)

    def weighted_sentiment(hours: float) -> float:
        selected = [
            row for row in rows
            if (cutoff - row["_published"]).total_seconds() <= hours * 3600
        ]
        denominator = sum(row["_weight"] for row in selected)
        return (
            sum(row["_sentiment"] * row["_weight"] for row in selected) / denominator
            if denominator > 0 else 0.0
        )

    sentiments = np.asarray([row["_sentiment"] for row in rows], dtype=float)
    weights = np.asarray([row["_weight"] for row in rows], dtype=float)
    if len(rows) and weights.sum() > 0:
        mean = float(np.average(sentiments, weights=weights))
        dispersion = float(np.sqrt(np.average((sentiments - mean) ** 2, weights=weights)))
    else:
        dispersion = 0.0

    negative = np.asarray([-x for x in sentiments if x < 0], dtype=float)
    negative_tail = float(np.quantile(negative, 0.90)) if len(negative) else 0.0
    event_risk = max(
        (
            row["_severity"] * row["_weight"] * (1.0 + max(0.0, -row["_sentiment"]))
            for row in rows
        ),
        default=0.0,
    )
    event_risk = float(min(1.0, event_risk))

    if rows:
        hours = pd.date_range(
            start=min(row["_published"] for row in rows).floor("h"),
            end=cutoff.floor("h"),
            freq="h",
        )
        counts = pd.Series(0.0, index=hours)
        for row in rows:
            stamp = row["_published"].floor("h")
            if stamp in counts.index:
                counts.loc[stamp] += 1.0
        baseline = counts.iloc[:-1] if len(counts) > 1 else counts
        std = float(baseline.std(ddof=0)) if len(baseline) else 0.0
        current = float(counts.iloc[-1]) if len(counts) else 0.0
        news_volume_z = (
            (current - float(baseline.mean())) / std
            if std > 1e-12 else 0.0
        )
        latest = max(row["_published"] for row in rows)
        freshness_seconds = max(0.0, float((cutoff - latest).total_seconds()))
    else:
        news_volume_z = 0.0
        freshness_seconds = None

    providers = set()
    sources = set()
    for row in rows:
        providers.update(str(x) for x in row.get("providers", []) if x)
        sources.update(str(x) for x in row.get("original_sources", []) if x)

    states = dict(provider_states or {})
    usable_provider = any(state in {"OK", "EMPTY"} for state in states.values())
    status = (
        "FRESH"
        if rows and usable_provider
        else "FRESH_EMPTY"
        if usable_provider
        else "MISSING"
    )
    return {
        "status": status,
        "sentiment_1h": weighted_sentiment(1),
        "sentiment_6h": weighted_sentiment(6),
        "sentiment_24h": weighted_sentiment(24),
        "news_volume_z": float(news_volume_z),
        "negative_tail_score": float(max(0.0, min(1.0, negative_tail))),
        "event_risk_score": event_risk,
        "source_count": len(providers | sources),
        "freshness_seconds": freshness_seconds,
        "sentiment_dispersion": dispersion,
        "story_count": len(rows),
        "provider_states": states,
        "critical_context_available": usable_provider,
    }


def explicit_bar_clock_v243(
    frame: pd.DataFrame,
    *,
    decision_cutoff: Any,
    calendar_name: str = "NYSE",
    target_bar_minutes: int = 60,
    close_lag_seconds: int = 120,
    provider: str = "canonical",
) -> pd.DataFrame:
    columns = [
        "bar_start", "bar_end", "decision_available_at",
        "regular_session", "closed_at_cutoff", "provider",
    ]
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns)
    work = frame.copy()
    if "timestamp" in work.columns:
        work = work.set_index("timestamp")
    elif "date" in work.columns:
        work = work.set_index("date")
    work.index = pd.DatetimeIndex(pd.to_datetime(work.index, utc=True), name="timestamp")
    work = work.sort_index(kind="stable")
    cutoff = utc(decision_cutoff)

    cal = mcal.get_calendar(calendar_name)
    start_date = (work.index.min() - pd.Timedelta(days=3)).date().isoformat()
    end_date = (work.index.max() + pd.Timedelta(days=3)).date().isoformat()
    schedule = cal.schedule(start_date=start_date, end_date=end_date).copy()
    schedule["market_open"] = pd.to_datetime(schedule["market_open"], utc=True)
    schedule["market_close"] = pd.to_datetime(schedule["market_close"], utc=True)
    lag = pd.Timedelta(seconds=int(close_lag_seconds))
    period = pd.Timedelta(minutes=int(target_bar_minutes))

    records = []
    for stamp in work.index:
        match = schedule.loc[
            (schedule["market_open"] <= stamp)
            & (schedule["market_close"] > stamp)
        ]
        if match.empty:
            continue
        session = match.iloc[0]
        market_open = utc(session["market_open"])
        market_close = utc(session["market_close"])
        elapsed_minutes = int((stamp - market_open).total_seconds() // 60)
        if elapsed_minutes < 0:
            continue
        bucket = elapsed_minutes // int(target_bar_minutes)
        bar_start = market_open + pd.Timedelta(minutes=bucket * int(target_bar_minutes))
        if stamp != bar_start:
            continue
        bar_end = min(bar_start + period, market_close)
        available = bar_end + lag
        records.append({
            "timestamp": stamp,
            "bar_start": bar_start,
            "bar_end": bar_end,
            "decision_available_at": available,
            "regular_session": True,
            "closed_at_cutoff": bool(available <= cutoff),
            "provider": provider,
        })
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(records).set_index("timestamp").sort_index(kind="stable")


def market_data_freshness_v243(
    symbol: str,
    frame: pd.DataFrame,
    *,
    decision_cutoff: Any,
    cfg: dict[str, Any],
    provider: str,
) -> dict[str, Any]:
    clock = explicit_bar_clock_v243(
        frame,
        decision_cutoff=decision_cutoff,
        calendar_name=str(cfg["market_data"].get("calendar", "NYSE")),
        target_bar_minutes=int(cfg["market_data"].get("target_bar_minutes", 60)),
        close_lag_seconds=int(cfg["market_data"].get("bar_close_lag_seconds", 120)),
        provider=provider,
    )
    closed = clock.loc[clock["closed_at_cutoff"] == True] if not clock.empty else clock  # noqa: E712
    if closed.empty:
        return {
            "symbol": symbol.upper(),
            "status": "MISSING_OR_NO_CLOSED_BAR",
            "latest_bar_start": None,
            "latest_bar_end": None,
            "latest_decision_available_at": None,
            "provider": provider,
        }
    last = closed.iloc[-1]
    available = utc(last["decision_available_at"])
    age = max(0.0, float((utc(decision_cutoff) - available).total_seconds()))
    return {
        "symbol": symbol.upper(),
        "status": "FRESH",
        "latest_bar_start": utc(last["bar_start"]).isoformat(),
        "latest_bar_end": utc(last["bar_end"]).isoformat(),
        "latest_decision_available_at": available.isoformat(),
        "age_seconds": age,
        "provider": provider,
        "closed_bars_only": True,
        "regular_session_only": True,
    }


def _event_blocker_name(event_type: str) -> str:
    text = event_type.lower()
    if any(term in text for term in ("fomc", "federal reserve", "interest rate", "powell", "fed ")):
        return "FOMC_WINDOW"
    return "HIGH_IMPACT_MACRO_WINDOW"


def calendar_context_v243(
    events: Iterable[EconomicEventV243],
    *,
    decision_cutoff: Any,
    data_freshness: Iterable[dict[str, Any]],
    source_status: str,
    retrieved_at: Any,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    cutoff = utc(decision_cutoff)
    blockers: list[str] = []
    adjustment = 0.0
    if source_status not in {"OK", "EMPTY"}:
        blockers.append("ECONOMIC_CALENDAR_UNAVAILABLE")

    latest_bar_end = None
    for row in data_freshness:
        if str(row.get("symbol", "")).upper() not in {"SPY", "QQQ"}:
            continue
        raw = row.get("latest_bar_end")
        if not raw:
            continue
        stamp = utc(raw)
        latest_bar_end = stamp if latest_bar_end is None else max(latest_bar_end, stamp)

    high_pre = float(cfg["calendar"].get("high_impact_pre_minutes", 30))
    high_post = float(cfg["calendar"].get("high_impact_post_minutes", 30))
    medium_pre = float(cfg["calendar"].get("medium_impact_pre_minutes", 60))
    high_adj = float(cfg["calendar"].get("high_impact_adjustment", -0.20))
    med_adj = float(cfg["calendar"].get("medium_impact_adjustment", -0.08))

    rows = []
    for event in events:
        row = event.to_dict()
        scheduled = utc(event.scheduled_at)
        minutes = float((scheduled - cutoff).total_seconds() / 60.0)
        row["minutes_from_cutoff"] = minutes
        rows.append(row)
        if event.impact == "HIGH":
            if 0 <= minutes <= high_pre:
                blockers.append(_event_blocker_name(event.event_type))
                adjustment = min(adjustment, high_adj)
            elif minutes < 0:
                # After a high-impact release, new exposure stays blocked until
                # release data is causally visible and at least one relevant
                # market bar has fully closed after the scheduled event.
                release_pending = event.actual is None
                bar_pending = latest_bar_end is None or latest_bar_end <= scheduled
                if release_pending:
                    blockers.append("MACRO_RELEASE_DATA_PENDING")
                if bar_pending:
                    blockers.append("POST_EVENT_BAR_NOT_CLOSED")
                if release_pending or bar_pending:
                    adjustment = min(adjustment, high_adj)
        elif event.impact == "MEDIUM" and 0 <= minutes <= medium_pre:
            adjustment = min(adjustment, med_adj)

    return {
        "status": "FRESH" if source_status in {"OK", "EMPTY"} else "MISSING",
        "provider_status": source_status,
        "retrieved_at": utc(retrieved_at).isoformat(),
        "entry_blockers": sorted(set(blockers)),
        "calendar_adjustment": float(adjustment),
        "events": rows,
    }


@dataclass(frozen=True)
class MarketContextSnapshotV243:
    schema_version: str
    snapshot_id: str
    decision_cutoff: str
    symbols: tuple[str, ...]
    market_regime_json: str
    calendar_context_json: str
    news_context_json: str
    data_freshness_json: str
    provider_provenance_json: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "decision_cutoff": self.decision_cutoff,
            "symbols": list(self.symbols),
            "market_regime": json.loads(self.market_regime_json),
            "calendar_context": json.loads(self.calendar_context_json),
            "news_context": json.loads(self.news_context_json),
            "data_freshness": json.loads(self.data_freshness_json),
            "provider_provenance": json.loads(self.provider_provenance_json),
        }


def build_snapshot_v243(
    *,
    decision_cutoff: Any,
    symbols: Iterable[str],
    market_regime: dict[str, Any],
    calendar_context: dict[str, Any],
    news_context: dict[str, Any],
    data_freshness: list[dict[str, Any]],
    provider_provenance: list[dict[str, Any]],
) -> MarketContextSnapshotV243:
    cutoff = utc(decision_cutoff).isoformat()
    clean_symbols = tuple(sorted({str(symbol).upper() for symbol in symbols if str(symbol).strip()}))
    body = {
        "schema_version": SCHEMA,
        "decision_cutoff": cutoff,
        "symbols": list(clean_symbols),
        "market_regime": market_regime,
        "calendar_context": calendar_context,
        "news_context": news_context,
        "data_freshness": data_freshness,
        "provider_provenance": provider_provenance,
    }
    snapshot_id = "CTX-" + _hash(body)[:32]
    return MarketContextSnapshotV243(
        schema_version=SCHEMA,
        snapshot_id=snapshot_id,
        decision_cutoff=cutoff,
        symbols=clean_symbols,
        market_regime_json=_json(market_regime),
        calendar_context_json=_json(calendar_context),
        news_context_json=_json(news_context),
        data_freshness_json=_json(data_freshness),
        provider_provenance_json=_json(provider_provenance),
    )


def verify_snapshot_v243(snapshot: dict[str, Any]) -> bool:
    if str(snapshot.get("schema_version")) != SCHEMA:
        return False
    body = {
        "schema_version": snapshot["schema_version"],
        "decision_cutoff": snapshot["decision_cutoff"],
        "symbols": snapshot["symbols"],
        "market_regime": snapshot["market_regime"],
        "calendar_context": snapshot["calendar_context"],
        "news_context": snapshot["news_context"],
        "data_freshness": snapshot["data_freshness"],
        "provider_provenance": snapshot["provider_provenance"],
    }
    return str(snapshot.get("snapshot_id")) == "CTX-" + _hash(body)[:32]


def _snapshot_is_fresh(snapshot: dict[str, Any], now: Any, max_age_minutes: float) -> bool:
    cutoff = utc(snapshot["decision_cutoff"])
    age = float((utc(now) - cutoff).total_seconds())
    return 0 <= age <= float(max_age_minutes) * 60.0


def _sac_adjustment(
    agent_shadow: dict[str, Any] | None,
    cfg: dict[str, Any],
) -> float:
    if not agent_shadow:
        return 0.0
    rl = cfg["rl"]
    if str(rl.get("sac_mode")) != "SHADOW_CONTEXT_ONLY":
        return 0.0
    minimum = int(rl.get("minimum_sac_test_trades_for_context_influence", 30))
    candidates = [
        row for row in agent_shadow.get("generated", [])
        if str(row.get("algorithm", "")).upper() == "SAC"
        and int(row.get("test_trades") or 0) >= minimum
        and str(row.get("quality")) == "SHADOW_ELIGIBLE"
    ]
    if not candidates:
        return 0.0
    target = float(candidates[-1].get("target_exposure") or 0.0)
    centered = max(-1.0, min(1.0, (target - 0.5) * 2.0))
    cap = abs(float(rl.get("sac_max_abs_adjustment", 0.05)))
    return max(-cap, min(cap, centered * cap))


def apply_context_policy_v243(
    proposals: pd.DataFrame,
    *,
    snapshot: dict[str, Any],
    cfg: dict[str, Any],
    agent_shadow: dict[str, Any] | None = None,
    now: Any | None = None,
) -> pd.DataFrame:
    if proposals.empty:
        return proposals.copy()
    if not verify_snapshot_v243(snapshot):
        raise ValueError("MARKET_CONTEXT_SNAPSHOT_HASH_INVALID")

    reference_now = utc(now if now is not None else pd.Timestamp.now(tz="UTC"))
    snapshot_fresh = _snapshot_is_fresh(
        snapshot,
        reference_now,
        float(cfg.get("snapshot_max_age_minutes", 20)),
    )
    calendar = dict(snapshot.get("calendar_context") or {})
    news = dict(snapshot.get("news_context") or {})
    freshness = {
        str(row.get("symbol", "")).upper(): row
        for row in snapshot.get("data_freshness", [])
    }
    critical_symbols = {
        str(x).upper()
        for x in cfg["market_data"].get("critical_symbols", ["SPY", "QQQ"])
    }
    all_critical_market_fresh = all(
        str(freshness.get(symbol, {}).get("status")) == "FRESH"
        for symbol in critical_symbols
    )
    sac_adjustment = _sac_adjustment(agent_shadow, cfg)
    ppo_weight = float(cfg["rl"].get("ppo_weight", 0.0))
    if abs(ppo_weight) > 1e-12:
        raise ValueError("PPO_WEIGHT_MUST_REMAIN_ZERO")
    if bool(cfg["rl"].get("rl_direct_broker_control", False)):
        raise ValueError("RL_DIRECT_BROKER_CONTROL_MUST_REMAIN_FALSE")

    non_single = {str(x).upper() for x in cfg.get("non_single_stock_symbols", [])}
    minimum = float(cfg["policy"].get("minimum_adjusted_conviction", 0.65))
    output = []

    for raw in proposals.to_dict(orient="records"):
        row = dict(raw)
        symbol = str(row.get("symbol") or "").upper()
        before = str(row.get("decision") or "SKIP").upper()
        raw_conv = float(row.get("conviction") or 0.0)
        existing = [x for x in str(row.get("blockers") or "").split("|") if x]
        context_blockers: list[str] = []
        cal_adj = 0.0
        news_adj = 0.0
        effective_sac = 0.0

        if before == "BUY_NEW":
            if not snapshot_fresh:
                context_blockers.append("MARKET_CONTEXT_SNAPSHOT_STALE")
            if cfg["policy"].get("fail_closed_market_data", True) and not all_critical_market_fresh:
                context_blockers.append("CRITICAL_MARKET_DATA_NOT_FRESH")
            if cfg["policy"].get("fail_closed_calendar", True):
                if str(calendar.get("status")) != "FRESH":
                    context_blockers.append("ECONOMIC_CALENDAR_MISSING_OR_STALE")
                context_blockers.extend(str(x) for x in calendar.get("entry_blockers", []))
            cal_adj = float(calendar.get("calendar_adjustment") or 0.0)

            nctx = dict(news.get(symbol) or {})
            if symbol not in non_single and cfg["policy"].get("fail_closed_single_stock_news", True):
                if not bool(nctx.get("critical_context_available", False)):
                    context_blockers.append("CRITICAL_NEWS_CONTEXT_MISSING")
            if (
                bool(nctx.get("news_present"))
                and cfg["news"].get("require_finbert_for_new_entries_when_news_present", True)
                and not bool(nctx.get("finbert_ready", False))
            ):
                context_blockers.append("NLP_FINBERT_UNAVAILABLE")

            negative_tail = float(nctx.get("negative_tail_score") or 0.0)
            event_risk = float(nctx.get("event_risk_score") or 0.0)
            if negative_tail >= float(cfg["news"].get("negative_tail_block_threshold", 0.70)):
                context_blockers.append("NEGATIVE_NEWS_CLUSTER")
            if event_risk >= float(cfg["news"].get("event_risk_block_threshold", 0.70)):
                context_blockers.append("EVENT_RISK_CLUSTER")

            sentiment = float(nctx.get("sentiment_6h") or 0.0)
            if sentiment >= 0:
                news_adj = min(
                    float(cfg["news"].get("maximum_positive_adjustment", 0.08)),
                    sentiment * float(cfg["news"].get("maximum_positive_adjustment", 0.08)),
                )
            else:
                news_adj = -min(
                    float(cfg["news"].get("maximum_negative_adjustment", 0.25)),
                    abs(sentiment) * float(cfg["news"].get("maximum_negative_adjustment", 0.25)),
                )
            effective_sac = sac_adjustment

        adjusted = max(0.0, min(1.0, raw_conv + cal_adj + news_adj + effective_sac))
        after = before
        if before == "BUY_NEW":
            if existing or context_blockers or adjusted < minimum:
                after = "SKIP"
                if adjusted < minimum:
                    context_blockers.append("ADJUSTED_CONVICTION_BELOW_MINIMUM")
        else:
            after = before

        sizing_multiplier = (
            max(0.0, min(1.0, adjusted / raw_conv))
            if raw_conv > 1e-12 and after == "BUY_NEW"
            else 0.0 if before == "BUY_NEW" else 1.0
        )
        row.update({
            "snapshot_id": snapshot["snapshot_id"],
            "decision_cutoff": snapshot["decision_cutoff"],
            "raw_conviction": raw_conv,
            "calendar_adjustment": cal_adj,
            "news_adjustment": news_adj,
            "sac_shadow_adjustment": effective_sac,
            "adjusted_conviction": adjusted,
            "conviction": adjusted,
            "sizing_multiplier": sizing_multiplier,
            "decision_before_context": before,
            "decision_after_context": after,
            "decision": after,
            "context_blockers": "|".join(sorted(set(context_blockers))),
            "blockers": "|".join(sorted(set(existing + context_blockers))),
            "ppo_weight": 0.0,
            "sac_mode": "SHADOW_CONTEXT_ONLY",
            "rl_direct_broker_control": False,
        })
        output.append(row)
    return pd.DataFrame(output)


__all__ = [
    "EconomicEventV243",
    "MarketContextSnapshotV243",
    "apply_context_policy_v243",
    "build_snapshot_v243",
    "calendar_context_v243",
    "causal_news_rows_v243",
    "explicit_bar_clock_v243",
    "market_data_freshness_v243",
    "news_features_v243",
    "normalize_economic_event_v243",
    "verify_snapshot_v243",
]
