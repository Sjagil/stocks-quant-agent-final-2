from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

import httpx

from ..models import NewsArticle


class EODHDProvider:
    BASE = "https://eodhd.com/api"

    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("EODHD API key is required")
        self.api_key = api_key
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self.client.close()

    def fetch_news(
        self,
        *,
        symbol: str | None = None,
        topic: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NewsArticle]:
        params: dict[str, object] = {
            "api_token": self.api_key,
            "fmt": "json",
            "limit": limit,
            "offset": offset,
        }
        if symbol:
            params["s"] = symbol
        if topic:
            params["t"] = topic
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.client.get(f"{self.BASE}/news", params=params)
        response.raise_for_status()
        payload = response.json()
        articles: list[NewsArticle] = []
        for item in payload if isinstance(payload, list) else []:
            title = str(item.get("title") or "").strip()
            body = str(item.get("content") or item.get("description") or "").strip()
            url = str(item.get("link") or item.get("url") or "").strip()
            date_raw = item.get("date") or item.get("published_at")
            published = _parse_dt(date_raw)
            symbols = tuple(_normalize_symbols(item.get("symbols") or []))
            tags = tuple(str(x) for x in (item.get("tags") or []) if x)
            source = str(item.get("source") or item.get("provider") or "EODHD")
            article_id = hashlib.sha256(
                f"{published.isoformat()}|{title}|{url}".encode("utf-8")
            ).hexdigest()[:24]
            articles.append(
                NewsArticle(
                    article_id=article_id,
                    published_at=published,
                    title=title,
                    body=body,
                    source=source,
                    url=url,
                    symbols=symbols,
                    tags=tags,
                )
            )
        return articles

    def fetch_sentiment(
        self, symbols: Iterable[str], from_date: str | None = None, to_date: str | None = None
    ) -> dict:
        params: dict[str, object] = {
            "api_token": self.api_key,
            "fmt": "json",
            "s": ",".join(symbols),
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        response = self.client.get(f"{self.BASE}/sentiments", params=params)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}


def _parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # EODHD frequently returns second precision without timezone.
        dt = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _normalize_symbols(values: object) -> list[str]:
    if isinstance(values, str):
        values = [values]
    output: list[str] = []
    if isinstance(values, list):
        for value in values:
            symbol = str(value).strip().upper()
            if symbol:
                output.append(symbol)
    return output
