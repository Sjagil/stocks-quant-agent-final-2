from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from stocks.news.contracts import (
    RawNewsItem,
)


_WORD = re.compile(
    r"[a-z0-9]+",
    re.IGNORECASE,
)


def title_tokens(
    title: str,
) -> set[str]:
    return {
        token.lower()
        for token
        in _WORD.findall(
            title
        )
        if len(
            token
        ) > 2
    }


def jaccard(
    left: set[str],
    right: set[str],
) -> float:
    if not left or not right:
        return 0.0

    union = left | right

    return (
        len(
            left & right
        )
        /
        len(
            union
        )
    )


@dataclass
class StoryCluster:
    story_id: str
    items: list[RawNewsItem]


def cluster_news(
    items: list[RawNewsItem],
    *,
    similarity_threshold: float = 0.72,
    max_time_distance_hours: float = 36.0,
) -> list[StoryCluster]:
    ordered = sorted(
        items,
        key=lambda item:
        item.published_at,
    )

    clusters: list[
        StoryCluster
    ] = []

    for item in ordered:
        tokens = title_tokens(
            item.title
        )

        matched = None

        for cluster in reversed(
            clusters
        ):
            representative = (
                cluster.items[0]
            )

            hours = abs(
                (
                    item.published_at
                    -
                    representative.published_at
                ).total_seconds()
            ) / 3600.0

            if (
                hours
                >
                max_time_distance_hours
            ):
                continue

            similarity = jaccard(
                tokens,
                title_tokens(
                    representative.title
                ),
            )

            if (
                similarity
                >= similarity_threshold
            ):
                matched = cluster
                break

        if matched is not None:
            matched.items.append(
                item
            )
            continue

        identity = hashlib.sha256(
            (
                item.title.lower()
                + "|"
                + item.published_at.date().isoformat()
            ).encode(
                "utf-8"
            )
        ).hexdigest()[:24]

        clusters.append(
            StoryCluster(
                story_id=identity,
                items=[
                    item
                ],
            )
        )

    return clusters
