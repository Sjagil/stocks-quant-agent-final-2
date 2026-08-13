from __future__ import annotations

import math
from datetime import datetime, timezone

from stocks.news.contracts import (
    NewsEvidence,
    RawNewsItem,
)
from stocks.news.dedup import (
    cluster_news,
)
from stocks.news.nlp import (
    financial_sentiment,
)
from stocks.providers.quality import (
    authority_score,
)


def _as_item(
    raw: dict,
) -> RawNewsItem:
    published = raw[
        "published_at"
    ]

    if isinstance(
        published,
        str,
    ):
        published = (
            datetime.fromisoformat(
                published.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

    return RawNewsItem(
        provider=str(
            raw[
                "provider"
            ]
        ),
        provider_id=str(
            raw[
                "provider_id"
            ]
        ),
        published_at=published,
        title=str(
            raw[
                "title"
            ]
        ),
        url=str(
            raw.get(
                "url",
                "",
            )
        ),
        summary=str(
            raw.get(
                "summary",
                "",
            )
        ),
        source_name=str(
            raw.get(
                "source_name",
                "",
            )
        ),
        symbols=tuple(
            raw.get(
                "symbols",
                (),
            )
        ),
        categories=tuple(
            raw.get(
                "categories",
                (),
            )
        ),
        provider_sentiment=(
            raw.get(
                "provider_sentiment"
            )
        ),
        metadata=dict(
            raw.get(
                "metadata",
                {},
            )
        ),
    )


def build_news_evidence(
    raw_items: list[dict],
    *,
    target_symbol: str,
    now: datetime | None = None,
) -> list[NewsEvidence]:
    now = (
        now
        or datetime.now(
            timezone.utc
        )
    )

    items = [
        _as_item(
            raw
        )
        for raw
        in raw_items
        if raw.get(
            "title"
        )
    ]

    clusters = cluster_news(
        items
    )

    evidence = []

    for cluster in clusters:
        representative = max(
            cluster.items,
            key=lambda item:
            len(
                item.summary
            )
            + len(
                item.title
            ),
        )

        providers = tuple(
            sorted(
                {
                    item.provider
                    for item
                    in cluster.items
                }
            )
        )

        source_quality = (
            sum(
                authority_score(
                    provider
                )
                for provider
                in providers
            )
            /
            max(
                len(
                    providers
                ),
                1,
            )
        )

        combined_text = (
            representative.title
            + ". "
            + representative.summary
        )

        sentiment = (
            financial_sentiment(
                combined_text
            )
        )

        age_hours = max(
            (
                now
                -
                representative.published_at
            ).total_seconds()
            / 3600.0,
            0.0,
        )

        time_decay = math.exp(
            -age_hours
            / 36.0
        )

        symbol_mentions = sum(
            1
            for item
            in cluster.items
            if (
                target_symbol.upper()
                in {
                    symbol.upper()
                    for symbol
                    in item.symbols
                }
            )
        )

        relevance = min(
            1.0,
            0.50
            +
            0.15
            * symbol_mentions,
        )

        novelty = 1.0 / max(
            len(
                cluster.items
            ),
            1,
        )

        provider_confirmation = min(
            1.0,
            len(
                providers
            )
            / 3.0,
        )

        evidence_score = (
            relevance
            * source_quality
            * time_decay
            * (
                0.70
                +
                0.30
                * provider_confirmation
            )
        )

        evidence.append(
            NewsEvidence(
                story_id=(
                    cluster.story_id
                ),
                symbols=(
                    target_symbol.upper(),
                ),
                published_at=(
                    representative.published_at
                ),
                title=(
                    representative.title
                ),
                summary=(
                    representative.summary
                ),
                providers=providers,
                original_sources=tuple(
                    sorted(
                        {
                            item.source_name
                            for item
                            in cluster.items
                            if item.source_name
                        }
                    )
                ),
                urls=tuple(
                    sorted(
                        {
                            item.url
                            for item
                            in cluster.items
                            if item.url
                        }
                    )
                ),
                relevance=relevance,
                novelty=novelty,
                source_quality=(
                    source_quality
                ),
                sentiment=(
                    sentiment.score
                ),
                sentiment_confidence=(
                    sentiment.confidence
                ),
                event_type="UNCLASSIFIED",
                event_severity=0.0,
                age_hours=age_hours,
                time_decay=time_decay,
                evidence_score=(
                    evidence_score
                ),
            )
        )

    return sorted(
        evidence,
        key=lambda row:
        row.evidence_score,
        reverse=True,
    )
