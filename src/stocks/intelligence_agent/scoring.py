from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

import numpy as np

from .models import AssetClass, AssetView, NewsSignal


def aggregate_news(signals: Iterable[NewsSignal], now: datetime | None = None) -> dict[str, tuple[float, float]]:
    now = now or datetime.now(timezone.utc)
    grouped: dict[str, list[NewsSignal]] = defaultdict(list)
    for signal in signals:
        if signal.published_at <= now:
            grouped[signal.symbol].append(signal)

    result: dict[str, tuple[float, float]] = {}
    for symbol, rows in grouped.items():
        weights = np.array([
            max(0.01, r.confidence * r.relevance * r.novelty * r.source_quality * r.event_severity)
            for r in rows
        ])
        values = np.array([r.raw_score for r in rows])
        score = float(np.average(values, weights=weights))
        agreement = 1.0 - float(np.clip(np.std(values), 0.0, 1.0))
        volume_conf = 1.0 - math.exp(-len(rows) / 4.0)
        confidence = float(np.clip(0.55 * agreement + 0.45 * volume_conf, 0.0, 1.0))
        result[symbol] = (score, confidence)
    return result


def build_asset_view(
    *,
    symbol: str,
    asset_class: AssetClass,
    technical_score: float,
    news_score: float,
    news_confidence: float,
    macro_score: float = 0.0,
    risk_score: float = 0.0,
    technical_weight: float = 0.45,
    news_weight: float = 0.35,
    macro_weight: float = 0.20,
) -> AssetView:
    base = (
        technical_weight * technical_score
        + news_weight * news_score
        + macro_weight * macro_score
    )
    risk_penalty = max(0.0, risk_score) * 0.25
    alpha = float(np.clip(base - risk_penalty, -1.0, 1.0))
    confidence = float(np.clip(0.45 + 0.35 * news_confidence + 0.20 * (1.0 - min(abs(risk_score), 1.0)), 0.0, 1.0))
    # Conservative score->return mapping. Calibrate this from forward outcomes later.
    expected_return = float(alpha * confidence * 0.08)
    rationale = (
        f"technical={technical_score:+.2f}",
        f"news={news_score:+.2f}",
        f"macro={macro_score:+.2f}",
        f"risk={risk_score:+.2f}",
    )
    return AssetView(
        symbol=symbol,
        asset_class=asset_class,
        alpha_score=alpha,
        confidence=confidence,
        news_score=news_score,
        technical_score=technical_score,
        macro_score=macro_score,
        risk_score=risk_score,
        expected_return=expected_return,
        rationale=rationale,
    )
