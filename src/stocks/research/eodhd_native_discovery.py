
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pandas_market_calendars as mcal

from stocks.providers.eodhd import EODHD_BASE_URL
from stocks.providers.http import ProviderHTTPClient


@dataclass(frozen=True)
class NativeScreenerQuery:
    name: str
    research_lane: str
    sort: str
    filters: tuple[tuple[Any, ...], ...]
    mover_type: str | None = None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def _number(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def default_queries() -> tuple[NativeScreenerQuery, ...]:
    base = (
        ("exchange", "=", "us"),
        ("adjusted_close", ">", 5),
        ("avgvol_200d", ">", 300_000),
        ("market_capitalization", ">", 300_000_000),
    )
    return (
        NativeScreenerQuery(
            name="CORE_MOMENTUM",
            research_lane="CORE",
            sort="refund_5d_p.desc",
            filters=base + (("market_capitalization", ">", 25_000_000_000),),
            mover_type="CORE_MOMENTUM",
        ),
        NativeScreenerQuery(
            name="GEM_QUALITY",
            research_lane="GEM",
            sort="market_capitalization.asc",
            filters=base
            + (
                ("market_capitalization", "<", 25_000_000_000),
                ("earnings_share", ">", 0),
            ),
            mover_type="GEM_QUALITY",
        ),
        NativeScreenerQuery(
            name="TACTICAL_MOMENTUM",
            research_lane="TACTICAL",
            sort="refund_5d_p.desc",
            filters=base + (("refund_5d_p", ">", 2.0),),
            mover_type="POSITIVE_MOMENTUM",
        ),
        NativeScreenerQuery(
            name="TACTICAL_PULLBACK",
            research_lane="TACTICAL",
            sort="refund_1d_p.asc",
            filters=base + (("refund_1d_p", "<", -2.0),),
            mover_type="PULLBACK",
        ),
    )


def parse_screener_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "items"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [dict(row) for row in rows if isinstance(row, dict)]
    return []


def latest_completed_nyse_session(*, now: pd.Timestamp | None = None) -> pd.Timestamp:
    timestamp = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")

    calendar = mcal.get_calendar("NYSE")
    start = timestamp.normalize() - pd.Timedelta(days=14)
    schedule = calendar.schedule(start_date=start.date(), end_date=timestamp.date())
    completed = schedule.loc[
        pd.to_datetime(schedule["market_close"], utc=True) <= timestamp
    ]
    if completed.empty:
        raise ValueError("no completed NYSE session")
    return pd.Timestamp(completed.index[-1])


def _technical_score(*, daily_return: float, five_day_return: float, mode: str) -> float:
    if mode == "TACTICAL_PULLBACK":
        value = (
            52.0
            + min(abs(min(daily_return, 0.0)) * 4.0, 20.0)
            + max(five_day_return, 0.0) * 1.25
        )
    else:
        value = 50.0 + daily_return * 2.0 + five_day_return * 1.5
    return _clamp(value, 15.0, 95.0)


def _liquidity_score(average_volume: float) -> float:
    if average_volume <= 0:
        return 20.0
    scaled = 50.0 + 12.0 * math.log10(max(average_volume, 100_000.0) / 100_000.0)
    return _clamp(scaled, 35.0, 95.0)


def _risk_score(market_cap: float) -> float:
    if market_cap >= 25_000_000_000:
        return 72.0
    if market_cap >= 5_000_000_000:
        return 66.0
    if market_cap >= 1_000_000_000:
        return 59.0
    return 50.0


def _fundamental_score(earnings_share: float | None) -> float:
    if earnings_share is None:
        return 50.0
    return 68.0 if earnings_share > 0 else 38.0


def score_native_row(
    row: dict[str, Any],
    *,
    query: NativeScreenerQuery,
) -> dict[str, Any] | None:
    symbol = str(row.get("code") or row.get("Code") or "").strip().upper()
    if symbol.endswith(".US"):
        symbol = symbol[:-3]
    if not symbol:
        return None

    market_cap = _number(row.get("market_capitalization"))
    adjusted_close = _number(row.get("adjusted_close"))
    average_volume = _number(row.get("avgvol_200d"), 0.0)
    daily_return = _number(row.get("refund_1d_p"), 0.0)
    five_day_return = _number(row.get("refund_5d_p"), 0.0)
    earnings_share = _number(row.get("earnings_share"))

    if any(
        value is None
        for value in (
            market_cap,
            adjusted_close,
            average_volume,
            daily_return,
            five_day_return,
        )
    ):
        return None

    assert market_cap is not None
    assert adjusted_close is not None
    assert average_volume is not None
    assert daily_return is not None
    assert five_day_return is not None

    technical = _technical_score(
        daily_return=daily_return,
        five_day_return=five_day_return,
        mode=query.name,
    )
    liquidity = _liquidity_score(average_volume)
    risk = _risk_score(market_cap)
    fundamental = _fundamental_score(earnings_share)
    lane_bonus = {"CORE": 2.0, "GEM": 4.0, "TACTICAL": 3.0}.get(
        query.research_lane, 0.0
    )
    research_score = _clamp(
        0.42 * technical
        + 0.25 * liquidity
        + 0.18 * fundamental
        + 0.15 * risk
        + lane_bonus
    )

    return {
        "symbol": symbol,
        "asset_key": f"{symbol}.US",
        "asset_type": "STOCK",
        "name": row.get("name") or row.get("Name"),
        "exchange": row.get("exchange") or row.get("Exchange"),
        "sector": row.get("sector"),
        "industry": row.get("industry"),
        "source_classification": "WATCHLIST",
        "research_lane": query.research_lane,
        "native_query": query.name,
        "research_eligible": True,
        "trade_eligible": False,
        "trade_blockers": ["SHARIAH_DATA_UNAVAILABLE"],
        "research_blockers": [],
        "shariah_gate": "PENDING",
        "shariah_verification_required": True,
        "shariah_status": "SHARIAH_DATA_UNAVAILABLE",
        "total_score": research_score,
        "research_score": research_score,
        "fundamental_score": fundamental,
        "technical_score": technical,
        "liquidity_score": liquidity,
        "risk_score": risk,
        "macro_score": None,
        "market_cap": market_cap,
        "median_dollar_volume_20d": average_volume * adjusted_close,
        "daily_return": daily_return,
        "five_day_return": five_day_return,
        "adjusted_close": adjusted_close,
        "earnings_share": earnings_share,
        "mover_type": query.mover_type,
        "fundamental_coverage": 0.25 if earnings_share is not None else 0.0,
        "fundamental_applicability": "COMPANY_LEVEL",
        "selection_reasons": [f"EODHD_NATIVE_{query.name}"],
        "warnings": [
            "RESEARCH_ONLY_PENDING_SHARIAH",
            "NATIVE_SCREENER_NOT_HISTORICAL_PIT",
        ],
        "macro_context": {
            "macro_regime": "UNKNOWN",
            "macro_confidence": 0.0,
            "macro_data_status": "DATA_INCOMPLETE",
            "sector_macro_tailwind": "UNKNOWN",
            "region_macro_tailwind": "UNKNOWN",
            "currency_regime": "UNKNOWN",
            "commodity_regime": "UNKNOWN",
            "market_breadth": None,
        },
        "sec_context": {
            "status": "UNAVAILABLE",
            "causal_event_count": 0,
            "sec_intelligence_score": 0.0,
            "overlay": {"sec_overlay_points": 0.0, "entry_authorized": False},
            "authority": "RANKING_OVERLAY_ONLY",
            "standalone_entry_allowed": False,
            "delayed_context_only": True,
        },
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def merge_native_rows(
    query_rows: Iterable[tuple[NativeScreenerQuery, dict[str, Any]]],
    *,
    maximum_candidates: int,
) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for query, raw in query_rows:
        scored = score_native_row(raw, query=query)
        if scored is None:
            continue
        symbol = str(scored["symbol"])
        existing = selected.get(symbol)
        if existing is None or float(scored["research_score"]) > float(
            existing["research_score"]
        ):
            selected[symbol] = scored
        else:
            reasons = set(existing.get("selection_reasons", []))
            reasons.add(f"EODHD_NATIVE_{query.name}")
            existing["selection_reasons"] = sorted(reasons)

    return sorted(
        selected.values(),
        key=lambda row: (
            float(row["research_score"]),
            float(row["technical_score"]),
            float(row["liquidity_score"]),
            row["symbol"],
        ),
        reverse=True,
    )[: int(maximum_candidates)]


def build_native_contextual_payload(
    project_root: str | Path,
    *,
    api_key: str,
    as_of: str | None,
    limit: int,
    client: ProviderHTTPClient | None = None,
    current_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    if not str(api_key).strip():
        raise ValueError("EODHD API key is required")

    latest = latest_completed_nyse_session(now=current_time)
    screening_date = latest.date() if not as_of else pd.Timestamp(as_of).date()
    if screening_date != latest.date():
        raise ValueError(
            "native EODHD screener is current-state only; "
            f"requested {screening_date}, latest completed NYSE session is {latest.date()}"
        )

    own_client = client is None
    http = client or ProviderHTTPClient(
        user_agent="stocks-quant-agent/native-eodhd-discovery-v2.5"
    )
    per_query_limit = min(100, max(50, int(limit)))
    collected: list[tuple[NativeScreenerQuery, dict[str, Any]]] = []
    source_counts: dict[str, int] = {}

    try:
        for query in default_queries():
            payload = http.get_json(
                f"{EODHD_BASE_URL}/screener",
                params={
                    "api_token": api_key,
                    "fmt": "json",
                    "sort": query.sort,
                    "filters": json.dumps(
                        [list(item) for item in query.filters],
                        separators=(",", ":"),
                    ),
                    "limit": per_query_limit,
                    "offset": 0,
                },
            )
            rows = parse_screener_rows(payload)
            source_counts[query.name] = len(rows)
            collected.extend((query, row) for row in rows)
    finally:
        if own_client:
            http.close()

    records = merge_native_rows(collected, maximum_candidates=limit)
    decision_time = (
        pd.Timestamp.now(tz="UTC")
        if current_time is None
        else pd.Timestamp(current_time)
    )
    if decision_time.tzinfo is None:
        decision_time = decision_time.tz_localize("UTC")
    else:
        decision_time = decision_time.tz_convert("UTC")

    for row in records:
        row["data_timestamps"] = {"price_session": screening_date.isoformat()}
        row["sec_context"]["as_of"] = decision_time.isoformat()

    return {
        "schema": "stocks_reference_contextual_candidates_v2",
        "screening_date": screening_date.isoformat(),
        "decision_time": decision_time.isoformat(),
        "screened_count": int(sum(source_counts.values())),
        "research_pool_count": len(records),
        "candidate_count": len(records),
        "trade_eligible_count": 0,
        "classification_counts": {"WATCHLIST": len(records)},
        "rejection_reason_counts": {"SHARIAH_DATA_UNAVAILABLE": len(records)},
        "research_blocker_counts": {},
        "trade_blocker_counts": {"SHARIAH_DATA_UNAVAILABLE": len(records)},
        "shariah_gate_counts": {"PENDING": len(records)},
        "minimum_research_score": 0.0,
        "research_score_contract": (
            "EODHD_NATIVE_CURRENT_DISCOVERY_HEURISTIC_RESEARCH_RANK;"
            "NO_EXECUTION_AUTHORITY"
        ),
        "records": records,
        "source_inventory": {
            "provider": "EODHD",
            "endpoint": "/api/screener",
            "queries": source_counts,
            "provider_call_units": len(source_counts) * 5,
            "current_state_only": True,
        },
        "macro_regime": "UNKNOWN",
        "macro_data_status": "DATA_INCOMPLETE",
        "sec_error": "NATIVE_FALLBACK_SEC_NOT_HYDRATED",
        "sec_overlay_bound_points": 4.0,
        "sec_standalone_entry_allowed": False,
        "selection_hidden_optimization": False,
        "execution_authority": "NONE",
        "strategy_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
        "native_fallback": True,
    }
