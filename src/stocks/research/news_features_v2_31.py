from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_EVENT_HALF_LIFE_HOURS = {
    "social": 4.0,
    "commentary": 24.0,
    "analyst": 36.0,
    "earnings": 72.0,
    "guidance": 120.0,
    "m&a": 240.0,
    "regulation": 480.0,
    "structural": 720.0,
    "other": 48.0,
}


@dataclass(frozen=True)
class NewsEvent:
    symbol: str
    published_at: datetime
    raw_score: float
    confidence: float = 1.0
    relevance: float = 1.0
    novelty: float = 1.0
    source_quality: float = 1.0
    severity: float = 1.0
    source: str = "unknown"
    event_class: str = "other"
    cluster_id: str | None = None

    def __post_init__(self) -> None:
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("published_at must be timezone-aware")
        if not str(self.symbol).strip():
            raise ValueError("symbol is required")
        if not -1.0 <= float(self.raw_score) <= 1.0:
            raise ValueError("raw_score must be in [-1,1]")
        for field in ("confidence", "relevance", "novelty", "source_quality", "severity"):
            value = float(getattr(self, field))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be in [0,1]")


def event_decay(
    age_hours: float,
    *,
    half_life_hours: float,
) -> float:
    if half_life_hours <= 0:
        raise ValueError("half_life_hours must be positive")
    return float(math.exp(-math.log(2.0) * max(0.0, float(age_hours)) / float(half_life_hours)))


def _event_weight(
    event: NewsEvent,
    *,
    asof: datetime,
    cluster_size: int,
    half_lives: dict[str, float],
) -> float:
    age_hours = max(0.0, (asof - event.published_at).total_seconds() / 3600.0)
    half_life = float(half_lives.get(event.event_class.lower(), half_lives.get("other", 48.0)))
    duplicate_penalty = 1.0 / math.sqrt(max(cluster_size, 1))
    return float(
        max(1e-12, event.confidence)
        * max(1e-12, event.relevance)
        * max(1e-12, event.novelty)
        * max(1e-12, event.source_quality)
        * max(1e-12, event.severity)
        * event_decay(age_hours, half_life_hours=half_life)
        * duplicate_penalty
    )


def aggregate_news_features(
    events: Iterable[NewsEvent],
    *,
    asof: datetime | None = None,
    half_lives: dict[str, float] | None = None,
) -> pd.DataFrame:
    asof = asof or datetime.now(timezone.utc)
    if asof.tzinfo is None or asof.utcoffset() is None:
        raise ValueError("asof must be timezone-aware")
    decay_map = dict(DEFAULT_EVENT_HALF_LIFE_HOURS)
    if half_lives:
        decay_map.update({str(k).lower(): float(v) for k, v in half_lives.items()})

    usable = [event for event in events if event.published_at <= asof]
    cluster_sizes: dict[tuple[str, str], int] = {}
    for event in usable:
        cluster = event.cluster_id or f"__singleton__:{event.source}:{event.published_at.isoformat()}"
        key = (event.symbol.upper(), cluster)
        cluster_sizes[key] = cluster_sizes.get(key, 0) + 1

    rows: list[dict[str, float | int | str]] = []
    by_symbol: dict[str, list[NewsEvent]] = {}
    for event in usable:
        by_symbol.setdefault(event.symbol.upper(), []).append(event)

    for symbol, group in sorted(by_symbol.items()):
        weights: list[float] = []
        scores: list[float] = []
        sources: set[str] = set()
        clusters: set[str] = set()
        for event in group:
            cluster = event.cluster_id or f"__singleton__:{event.source}:{event.published_at.isoformat()}"
            weight = _event_weight(
                event,
                asof=asof,
                cluster_size=cluster_sizes[(symbol, cluster)],
                half_lives=decay_map,
            )
            weights.append(weight)
            scores.append(float(event.raw_score))
            sources.add(str(event.source).strip().lower())
            clusters.add(cluster)
        w = np.asarray(weights, dtype=float)
        s = np.asarray(scores, dtype=float)
        weighted_sentiment = float(np.average(s, weights=w)) if w.sum() > 0 else 0.0
        weighted_variance = float(np.average((s - weighted_sentiment) ** 2, weights=w)) if w.sum() > 0 else 0.0
        agreement = float(np.clip(1.0 - math.sqrt(max(weighted_variance, 0.0)), 0.0, 1.0))
        source_diversity = len(sources) / max(len(group), 1)
        independent_cluster_ratio = len(clusters) / max(len(group), 1)
        intensity = float(w.sum())
        rows.append(
            {
                "symbol": symbol,
                "news_weighted_sentiment": weighted_sentiment,
                "news_agreement": agreement,
                "news_source_diversity": float(source_diversity),
                "news_independent_cluster_ratio": float(independent_cluster_ratio),
                "news_event_intensity": intensity,
                "news_event_count": len(group),
                "news_independent_clusters": len(clusters),
                "news_unique_sources": len(sources),
            }
        )
    return pd.DataFrame(rows)


def news_surprise(
    current_score: pd.Series,
    *,
    lookback: int = 20,
) -> pd.Series:
    if lookback < 3:
        raise ValueError("lookback must be >= 3")
    values = pd.to_numeric(current_score, errors="coerce").astype(float)
    prior_mean = values.shift(1).rolling(lookback, min_periods=lookback).mean()
    prior_std = values.shift(1).rolling(lookback, min_periods=lookback).std(ddof=0)
    return (values - prior_mean) / prior_std.replace(0.0, np.nan)


__all__ = [
    "DEFAULT_EVENT_HALF_LIFE_HOURS",
    "NewsEvent",
    "aggregate_news_features",
    "event_decay",
    "news_surprise",
]
