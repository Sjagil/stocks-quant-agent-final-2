from datetime import datetime, timezone

from stocks.news.contracts import RawNewsItem
from stocks.news.dedup import cluster_news


def item(
    provider: str,
    title: str,
) -> RawNewsItem:
    return RawNewsItem(
        provider=provider,
        provider_id=provider,
        published_at=datetime(
            2026,
            8,
            13,
            tzinfo=timezone.utc,
        ),
        title=title,
        url=f"https://example.com/{provider}",
    )


def test_same_story_across_providers_is_one_cluster() -> None:
    rows = [
        item(
            "provider_a",
            "Nvidia shares rise after strong AI demand outlook",
        ),
        item(
            "provider_b",
            "Nvidia shares rise after strong AI demand outlook",
        ),
    ]

    clusters = cluster_news(
        rows
    )

    assert len(clusters) == 1
    assert len(
        clusters[0].items
    ) == 2


def test_different_story_is_not_collapsed() -> None:
    rows = [
        item(
            "provider_a",
            "Nvidia shares rise after strong AI demand outlook",
        ),
        item(
            "provider_b",
            "Federal Reserve keeps interest rates unchanged",
        ),
    ]

    clusters = cluster_news(
        rows
    )

    assert len(clusters) == 2
