from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AssetClass(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    COMMODITY = "commodity"


class EventType(str, Enum):
    EARNINGS = "earnings"
    GUIDANCE = "guidance"
    M_AND_A = "m_and_a"
    ANALYST = "analyst"
    REGULATORY = "regulatory"
    LITIGATION = "litigation"
    SUPPLY = "supply"
    DEMAND = "demand"
    MACRO = "macro"
    GEOPOLITICAL = "geopolitical"
    MANAGEMENT = "management"
    CAPITAL = "capital"
    OTHER = "other"


@dataclass(frozen=True)
class NewsArticle:
    article_id: str
    published_at: datetime
    title: str
    body: str
    source: str
    url: str
    symbols: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class NewsSignal:
    symbol: str
    published_at: datetime
    sentiment: float
    confidence: float
    relevance: float
    novelty: float
    source_quality: float
    event_type: EventType
    event_severity: float
    horizon_days: int
    raw_score: float
    article_id: str
    rationale: str


@dataclass(frozen=True)
class IndicatorSnapshot:
    symbol: str
    asof: datetime
    values: dict[str, float]
    technical_score: float
    quality_score: float = 1.0


@dataclass(frozen=True)
class AssetView:
    symbol: str
    asset_class: AssetClass
    alpha_score: float
    confidence: float
    news_score: float
    technical_score: float
    macro_score: float = 0.0
    risk_score: float = 0.0
    expected_return: float = 0.0
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class AllocationTarget:
    symbol: str
    asset_class: AssetClass
    current_weight: float
    target_weight: float
    delta_weight: float
    target_notional: float
    action: str
    confidence: float
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortfolioPlan:
    created_at: datetime
    equity: float
    cash_weight: float
    targets: tuple[AllocationTarget, ...]
    execution_authority: str = "NONE"
    risk_flags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
