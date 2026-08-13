from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from stocks.data.canonical import (
    canonicalize_ohlcv,
)
from stocks.news.contracts import RawNewsItem


def yahoo_bars(
    symbol: str,
    *,
    period: str = "2y",
    interval: str = "1d",
) -> pd.DataFrame:
    ticker = yf.Ticker(
        symbol
    )

    frame = ticker.history(
        period=period,
        interval=interval,
        auto_adjust=False,
        actions=True,
    )

    if frame.empty:
        raise ValueError(
            f"Yahoo returned no bars "
            f"for {symbol}"
        )

    frame = frame.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    return canonicalize_ohlcv(
        frame
    )


def _published_at(
    value: Any,
) -> datetime:
    if isinstance(
        value,
        (int, float),
    ):
        return datetime.fromtimestamp(
            float(value),
            tz=timezone.utc,
        )

    if isinstance(
        value,
        str,
    ):
        parsed = pd.Timestamp(
            value
        )

        if parsed.tzinfo is None:
            parsed = (
                parsed.tz_localize(
                    "UTC"
                )
            )
        else:
            parsed = (
                parsed.tz_convert(
                    "UTC"
                )
            )

        return parsed.to_pydatetime()

    return datetime.now(
        timezone.utc
    )


def yahoo_news(
    symbol: str,
) -> list[RawNewsItem]:
    ticker = yf.Ticker(
        symbol
    )

    rows = ticker.news or []

    output: list[
        RawNewsItem
    ] = []

    for row in rows:
        content = (
            row.get(
                "content",
                row,
            )
            if isinstance(
                row,
                dict,
            )
            else {}
        )

        title = str(
            content.get(
                "title",
                "",
            )
        ).strip()

        if not title:
            continue

        canonical_url = (
            content.get(
                "canonicalUrl",
                {}
            )
        )

        if isinstance(
            canonical_url,
            dict,
        ):
            url = str(
                canonical_url.get(
                    "url",
                    "",
                )
            )
        else:
            url = str(
                canonical_url or ""
            )

        published = _published_at(
            content.get(
                "pubDate"
            )
            or row.get(
                "providerPublishTime"
            )
        )

        provider_id = hashlib.sha256(
            (
                symbol
                + "|"
                + title
                + "|"
                + url
            ).encode(
                "utf-8"
            )
        ).hexdigest()[:24]

        output.append(
            RawNewsItem(
                provider="yfinance",
                provider_id=provider_id,
                published_at=published,
                title=title,
                url=url,
                summary=str(
                    content.get(
                        "summary",
                        "",
                    )
                ),
                source_name=str(
                    content.get(
                        "provider",
                        ""
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
                metadata={
                    "raw_type": (
                        content.get(
                            "contentType"
                        )
                    )
                },
            )
        )

    return output
