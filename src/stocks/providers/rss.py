from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable

import feedparser

from stocks.news.contracts import RawNewsItem


def _datetime(
    value: str | None,
) -> datetime:
    if not value:
        return datetime.now(
            timezone.utc
        )

    try:
        parsed = (
            parsedate_to_datetime(
                value
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except Exception:
        return datetime.now(
            timezone.utc
        )


def fetch_feed(
    url: str,
    *,
    source_name: str,
    symbols: Iterable[str] = (),
) -> list[RawNewsItem]:
    feed = feedparser.parse(
        url
    )

    output = []

    for entry in feed.entries:
        title = str(
            entry.get(
                "title",
                "",
            )
        ).strip()

        link = str(
            entry.get(
                "link",
                "",
            )
        ).strip()

        if not title:
            continue

        published_at = _datetime(
            entry.get(
                "published"
            )
            or entry.get(
                "updated"
            )
        )

        identity = hashlib.sha256(
            (
                source_name
                + "|"
                + title
                + "|"
                + link
            ).encode(
                "utf-8"
            )
        ).hexdigest()[:24]

        output.append(
            RawNewsItem(
                provider="rss",
                provider_id=identity,
                published_at=published_at,
                title=title,
                url=link,
                summary=str(
                    entry.get(
                        "summary",
                        "",
                    )
                ),
                source_name=source_name,
                symbols=tuple(
                    symbol.upper()
                    for symbol
                    in symbols
                ),
            )
        )

    return output
