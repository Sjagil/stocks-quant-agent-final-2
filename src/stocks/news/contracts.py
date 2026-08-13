from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawNewsItem:
    provider: str
    provider_id: str
    published_at: datetime
    title: str
    url: str
    summary: str = ""
    source_name: str = ""
    symbols: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    provider_sentiment: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["published_at"] = (
            self.published_at.isoformat()
        )
        payload["symbols"] = list(
            self.symbols
        )
        payload["categories"] = list(
            self.categories
        )
        return payload


@dataclass(frozen=True)
class NewsEvidence:
    story_id: str
    symbols: tuple[str, ...]
    published_at: datetime
    title: str
    summary: str
    providers: tuple[str, ...]
    original_sources: tuple[str, ...]
    urls: tuple[str, ...]

    relevance: float
    novelty: float
    source_quality: float

    sentiment: float
    sentiment_confidence: float

    event_type: str
    event_severity: float

    age_hours: float
    time_decay: float

    evidence_score: float

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)

        payload[
            "published_at"
        ] = self.published_at.isoformat()

        return payload
