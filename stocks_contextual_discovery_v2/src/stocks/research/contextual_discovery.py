from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

SOURCE_CLASSIFICATIONS = frozenset({"HIGH_POTENTIAL", "WATCHLIST", "NEUTRAL"})

@dataclass(frozen=True)
class ContextualDiscoveryPolicy:
    gem_market_cap_ceiling_usd: float
    tactical_min_technical_score: float
    tactical_min_absolute_daily_return: float
    minimum_research_pool_total_score: float
    maximum_sec_overlay_points: float
    maximum_candidates: int

    @classmethod
    def load(cls, path: Path) -> "ContextualDiscoveryPolicy":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema") != "contextual_candidate_discovery_policy_v2":
            raise ValueError("invalid contextual discovery policy schema")
        result = cls(
            gem_market_cap_ceiling_usd=float(raw["gem_market_cap_ceiling_usd"]),
            tactical_min_technical_score=float(raw["tactical_min_technical_score"]),
            tactical_min_absolute_daily_return=float(raw["tactical_min_absolute_daily_return"]),
            minimum_research_pool_total_score=float(raw["minimum_research_pool_total_score"]),
            maximum_sec_overlay_points=float(raw["maximum_sec_overlay_points"]),
            maximum_candidates=int(raw["maximum_candidates"]),
        )
        if result.gem_market_cap_ceiling_usd <= 0:
            raise ValueError("invalid gem market-cap ceiling")
        if not 0 <= result.minimum_research_pool_total_score <= 100:
            raise ValueError("invalid research-pool score floor")
        if not 0 < result.maximum_sec_overlay_points <= 10:
            raise ValueError("invalid SEC overlay bound")
        if not 0 < result.maximum_candidates <= 500:
            raise ValueError("invalid candidate maximum")
        return result

def _finite(value: Any, *, field: str, allow_none: bool = False) -> float | None:
    if value in (None, ""):
        if allow_none:
            return None
        raise ValueError(f"{field}: value missing")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field}: non-finite value")
    return result

def _validate_timestamp(value: Any, *, decision_time: pd.Timestamp, field: str) -> None:
    if value in (None, ""):
        return
    timestamp = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(timestamp):
        raise ValueError(f"{field}: invalid timestamp")
    if timestamp > decision_time:
        raise ValueError(f"{field}: future information")

def _macro_fields(record: dict[str, Any]) -> dict[str, Any]:
    context = dict(record.get("macro_context") or {})
    return {
        "macro_regime": context.get("macro_regime", "UNKNOWN"),
        "macro_confidence": context.get("macro_confidence", 0.0),
        "macro_data_status": context.get("macro_data_status", "DATA_INCOMPLETE"),
        "sector_macro_tailwind": context.get("sector_macro_tailwind", "UNKNOWN"),
        "region_macro_tailwind": context.get("region_macro_tailwind", "UNKNOWN"),
        "currency_regime": context.get("currency_regime", "UNKNOWN"),
        "commodity_regime": context.get("commodity_regime", "UNKNOWN"),
        "market_breadth": context.get("market_breadth"),
    }

def canonicalize_contextual_candidates(payload: dict[str, Any], policy: ContextualDiscoveryPolicy) -> tuple[pd.DataFrame, dict[str, Any]]:
    if payload.get("schema") != "stocks_reference_contextual_candidates_v2":
        raise ValueError("invalid contextual reference screener schema")
    if payload.get("execution_authority") != "NONE" or payload.get("strategy_authority") != "NONE" or int(payload.get("broker_calls", 0)) != 0 or int(payload.get("order_calls", 0)) != 0:
        raise ValueError("contextual reference screener attempted authority escalation")
    decision_time = pd.to_datetime(payload["decision_time"], utc=True, errors="raise")
    screening_date = pd.Timestamp(payload["screening_date"]).date()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in payload.get("records") or []:
        symbol = str(record.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError("candidate symbol missing")
        if symbol in seen:
            raise ValueError(f"duplicate candidate: {symbol}")
        seen.add(symbol)
        classification = str(record.get("source_classification") or record.get("classification") or "")
        if classification not in SOURCE_CLASSIFICATIONS:
            raise ValueError(f"{symbol}: invalid source classification")
        if record.get("rejection_reasons") or []:
            raise ValueError(f"{symbol}: research-pool row has hard rejection reasons")
        if record.get("execution_authority") != "NONE":
            raise ValueError(f"{symbol}: execution authority escalation")
        timestamps = dict(record.get("data_timestamps") or {})
        for field in ("price_source_timestamp", "fundamental_available_at", "shariah_screened_at"):
            _validate_timestamp(timestamps.get(field), decision_time=decision_time, field=f"{symbol}.{field}")
        price_session = timestamps.get("price_session")
        if price_session and pd.Timestamp(price_session).date() > screening_date:
            raise ValueError(f"{symbol}: future price session")
        total_score = _finite(record.get("total_score"), field=f"{symbol}.total_score")
        fundamental_score = _finite(record.get("fundamental_score"), field=f"{symbol}.fundamental_score")
        technical_score = _finite(record.get("technical_score"), field=f"{symbol}.technical_score")
        liquidity_score = _finite(record.get("liquidity_score"), field=f"{symbol}.liquidity_score")
        risk_score = _finite(record.get("risk_score"), field=f"{symbol}.risk_score")
        macro_score = _finite(record.get("macro_score"), field=f"{symbol}.macro_score", allow_none=True)
        market_cap = _finite(record.get("market_cap"), field=f"{symbol}.market_cap", allow_none=True)
        daily_return = _finite(record.get("daily_return"), field=f"{symbol}.daily_return", allow_none=True)
        if total_score < policy.minimum_research_pool_total_score:
            raise ValueError(f"{symbol}: below research-pool score floor")
        sec_context = dict(record.get("sec_context") or {})
        sec_overlay = dict(sec_context.get("overlay") or {})
        sec_points = _finite(sec_overlay.get("sec_overlay_points", 0.0), field=f"{symbol}.sec_overlay_points")
        if abs(sec_points) > policy.maximum_sec_overlay_points + 1e-9:
            raise ValueError(f"{symbol}: SEC overlay exceeds canonical bound")
        if sec_context:
            authority = sec_context.get("authority")
            if authority not in (None, "RANKING_OVERLAY_ONLY"):
                raise ValueError(f"{symbol}: invalid SEC authority")
            if bool(sec_context.get("standalone_entry_allowed", False)):
                raise ValueError(f"{symbol}: SEC attempted standalone entry authority")
            _validate_timestamp(sec_context.get("as_of"), decision_time=decision_time, field=f"{symbol}.sec_as_of")
        contextual_score = max(0.0, min(100.0, float(total_score + sec_points)))
        asset_type = str(record.get("asset_type") or "UNKNOWN").upper()
        mover_type = str(record.get("mover_type") or "").upper()
        tactical_candidate = ((bool(mover_type) or (daily_return is not None and abs(daily_return) >= policy.tactical_min_absolute_daily_return)) and technical_score >= policy.tactical_min_technical_score)
        if classification == "HIGH_POTENTIAL":
            lane = "GEM" if asset_type == "STOCK" and market_cap is not None and market_cap < policy.gem_market_cap_ceiling_usd else "CORE"
        elif tactical_candidate:
            lane = "TACTICAL"
        else:
            lane = "WATCHLIST"
        macro = _macro_fields(record)
        rows.append({
            "symbol": symbol, "asset_key": record.get("asset_key"), "asset_type": asset_type,
            "sector": record.get("sector"), "industry": record.get("industry"),
            "source_classification": classification, "lane": lane, "core_candidate": lane == "CORE",
            "gem_candidate": lane == "GEM", "tactical_candidate": tactical_candidate,
            "total_score": total_score, "contextual_score": contextual_score,
            "fundamental_score": fundamental_score, "technical_score": technical_score,
            "liquidity_score": liquidity_score, "risk_score": risk_score, "macro_score": macro_score, **macro,
            "sec_status": sec_context.get("status", "UNAVAILABLE"),
            "sec_event_count": int(sec_context.get("causal_event_count", 0) or 0),
            "sec_intelligence_score": float(sec_context.get("sec_intelligence_score", 0.0) or 0.0),
            "sec_overlay_points": sec_points, "market_cap": market_cap,
            "median_dollar_volume_20d": record.get("median_dollar_volume_20d"),
            "bid_ask_spread_bps": record.get("bid_ask_spread_bps"), "daily_return": daily_return,
            "mover_type": mover_type or None, "shariah_status": record.get("shariah_status"),
            "selection_reasons": record.get("selection_reasons") or [], "warnings": record.get("warnings") or [],
            "decision_time": decision_time, "screening_date": screening_date,
            "source": "STOCKS_REFERENCE_CONTEXTUAL_PIT_SCREENER",
            "strategy_assignment": "NOT_YET_GENERALIZED", "execution_authority": "NONE", "broker_calls": 0,
        })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        lane_rank = {"GEM": 0, "CORE": 1, "TACTICAL": 2, "WATCHLIST": 3}
        frame["_lane_rank"] = frame["lane"].map(lane_rank)
        frame = frame.sort_values(["_lane_rank", "contextual_score", "total_score", "technical_score", "symbol"], ascending=[True, False, False, False, True]).drop(columns=["_lane_rank"]).head(policy.maximum_candidates).reset_index(drop=True)
    def count_equals(column: str, value: Any) -> int:
        return 0 if frame.empty else int((frame[column] == value).sum())
    audit = {
        "schema": "canonical_contextual_candidate_discovery_v2", "screening_date": str(screening_date),
        "decision_time": decision_time.isoformat(), "candidate_count": int(len(frame)),
        "core_count": count_equals("lane", "CORE"), "gem_count": count_equals("lane", "GEM"),
        "tactical_count": count_equals("lane", "TACTICAL"), "watchlist_count": count_equals("lane", "WATCHLIST"),
        "neutral_source_count": count_equals("source_classification", "NEUTRAL"),
        "sec_covered_count": int((frame["sec_event_count"] > 0).sum()) if not frame.empty else 0,
        "sec_positive_overlay_count": int((frame["sec_overlay_points"] > 0).sum()) if not frame.empty else 0,
        "sec_negative_overlay_count": int((frame["sec_overlay_points"] < 0).sum()) if not frame.empty else 0,
        "macro_go_count": count_equals("macro_data_status", "GO"),
        "ranking_score": "DONOR_TOTAL_SCORE_PLUS_BOUNDED_SEC_OVERLAY",
        "macro_already_embedded_in_donor_total_score": True, "sec_standalone_entry_allowed": False,
        "validated_strategy_assignment": False,
        "reason": "dynamic-universe strategy generalization must run before strategy assignment",
        "execution_authority": "NONE", "broker_calls": 0, "order_calls": 0,
    }
    return frame, audit
