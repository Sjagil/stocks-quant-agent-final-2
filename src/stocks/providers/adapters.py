from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from stocks.news.contracts import RawNewsItem
from stocks.providers.contracts import (
    SourceProvenance,
    SourceResult,
    SourceState,
)
from stocks.providers.env import secret
from stocks.providers.http import ProviderHTTPClient
from stocks.providers.rss import fetch_feed


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(
    value: Any,
) -> datetime:
    if value is None:
        return _now()

    if isinstance(
        value,
        (int, float),
    ):
        return datetime.fromtimestamp(
            float(value),
            tz=timezone.utc,
        )

    try:
        parsed = pd.Timestamp(value)

        if parsed.tzinfo is None:
            parsed = parsed.tz_localize(
                "UTC"
            )
        else:
            parsed = parsed.tz_convert(
                "UTC"
            )

        return parsed.to_pydatetime()

    except Exception:
        return _now()


def _news_id(
    provider: str,
    title: str,
    url: str,
) -> str:
    return hashlib.sha256(
        (
            provider
            + "|"
            + title
            + "|"
            + url
        ).encode("utf-8")
    ).hexdigest()[:24]


def _unconfigured(
    provider: str,
    domain: str,
) -> SourceResult:
    return SourceResult(
        provider=provider,
        domain=domain,
        state=SourceState.UNCONFIGURED,
    ).finish()


def _error(
    provider: str,
    domain: str,
    exc: Exception,
) -> SourceResult:
    return SourceResult(
        provider=provider,
        domain=domain,
        state=SourceState.ERROR,
        error=(
            f"{type(exc).__name__}: {exc}"
        ),
    ).finish()


def polygon_snapshot(
    symbol: str,
) -> SourceResult:
    key = secret(
        "POLYGON_API_KEY"
    )

    if not key:
        return _unconfigured(
            "polygon",
            "live_quotes",
        )

    try:
        url = (
            "https://api.polygon.io/v2/"
            "snapshot/locale/us/markets/stocks/"
            f"tickers/{symbol.upper()}"
        )

        with ProviderHTTPClient() as client:
            payload = client.get_json(
                url,
                params={
                    "apiKey": key,
                },
            )

        ticker = (
            payload.get(
                "ticker",
                {}
            )
            if isinstance(
                payload,
                dict,
            )
            else {}
        )

        return SourceResult(
            provider="polygon",
            domain="live_quotes",
            state=(
                SourceState.OK
                if ticker
                else SourceState.EMPTY
            ),
            items=[
                ticker
            ] if ticker else [],
            provenance=[
                SourceProvenance(
                    provider="polygon",
                    domain="live_quotes",
                    endpoint=(
                        "/v2/snapshot/locale/us/"
                        "markets/stocks/tickers"
                    ),
                    symbol=symbol.upper(),
                )
            ],
        ).finish()

    except Exception as exc:
        return _error(
            "polygon",
            "live_quotes",
            exc,
        )


def twelvedata_bars(
    symbol: str,
    *,
    interval: str = "15min",
    outputsize: int = 100,
) -> SourceResult:
    key = secret(
        "TWELVEDATA_API_KEY"
    )

    if not key:
        return _unconfigured(
            "twelvedata",
            "bars",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "outputsize": outputsize,
                    "order": "ASC",
                    "apikey": key,
                },
            )

        if (
            isinstance(payload, dict)
            and payload.get("status") == "error"
        ):
            raise RuntimeError(
                payload.get(
                    "message",
                    "Twelve Data error",
                )
            )

        values = (
            payload.get(
                "values",
                [],
            )
            if isinstance(
                payload,
                dict,
            )
            else []
        )

        return SourceResult(
            provider="twelvedata",
            domain="bars",
            state=(
                SourceState.OK
                if values
                else SourceState.EMPTY
            ),
            items=list(values),
            provenance=[
                SourceProvenance(
                    provider="twelvedata",
                    domain="bars",
                    endpoint="/time_series",
                    symbol=symbol.upper(),
                    metadata={
                        "interval": interval,
                    },
                )
            ],
        ).finish()

    except Exception as exc:
        return _error(
            "twelvedata",
            "bars",
            exc,
        )


def finnhub_quote(
    symbol: str,
) -> SourceResult:
    key = secret(
        "FINNHUB_API_KEY"
    )

    if not key:
        return _unconfigured(
            "finnhub",
            "live_quotes",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://finnhub.io/api/v1/quote",
                params={
                    "symbol": symbol.upper(),
                    "token": key,
                },
            )

        valid = bool(
            isinstance(
                payload,
                dict,
            )
            and payload.get("c")
        )

        return SourceResult(
            provider="finnhub",
            domain="live_quotes",
            state=(
                SourceState.OK
                if valid
                else SourceState.EMPTY
            ),
            items=[
                payload
            ] if valid else [],
            provenance=[
                SourceProvenance(
                    provider="finnhub",
                    domain="live_quotes",
                    endpoint="/quote",
                    symbol=symbol.upper(),
                )
            ],
        ).finish()

    except Exception as exc:
        return _error(
            "finnhub",
            "live_quotes",
            exc,
        )


def finnhub_news(
    symbol: str,
    *,
    lookback_days: int = 7,
) -> SourceResult:
    key = secret(
        "FINNHUB_API_KEY"
    )

    if not key:
        return _unconfigured(
            "finnhub",
            "news",
        )

    end = _now().date()

    start = (
        end
        - timedelta(
            days=lookback_days
        )
    )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": symbol.upper(),
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                    "token": key,
                },
            )

        rows = (
            payload
            if isinstance(
                payload,
                list,
            )
            else []
        )

        items = []

        for row in rows:
            title = str(
                row.get(
                    "headline",
                    "",
                )
            ).strip()

            if not title:
                continue

            url = str(
                row.get(
                    "url",
                    "",
                )
            )

            item = RawNewsItem(
                provider="finnhub",
                provider_id=str(
                    row.get(
                        "id"
                    )
                    or _news_id(
                        "finnhub",
                        title,
                        url,
                    )
                ),
                published_at=_timestamp(
                    row.get(
                        "datetime"
                    )
                ),
                title=title,
                url=url,
                summary=str(
                    row.get(
                        "summary",
                        "",
                    )
                ),
                source_name=str(
                    row.get(
                        "source",
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
                categories=(
                    str(
                        row.get(
                            "category",
                            "",
                        )
                    ),
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="finnhub",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "finnhub",
            "news",
            exc,
        )


def marketstack_bars(
    symbol: str,
    *,
    interval: str = "15min",
) -> SourceResult:
    key = secret(
        "MARKETSTACK_API_KEY"
    )

    if not key:
        return _unconfigured(
            "marketstack",
            "bars",
        )

    versions = (
        "v2",
        "v1",
    )

    last_error = None

    for version in versions:
        try:
            with ProviderHTTPClient() as client:
                payload = client.get_json(
                    (
                        "https://api.marketstack.com/"
                        f"{version}/intraday"
                    ),
                    params={
                        "access_key": key,
                        "symbols": symbol.upper(),
                        "interval": interval,
                        "limit": 100,
                    },
                )

            rows = (
                payload.get(
                    "data",
                    [],
                )
                if isinstance(
                    payload,
                    dict,
                )
                else []
            )

            if isinstance(
                rows,
                dict,
            ):
                rows = rows.get(
                    "data",
                    [],
                )

            return SourceResult(
                provider="marketstack",
                domain="bars",
                state=(
                    SourceState.OK
                    if rows
                    else SourceState.EMPTY
                ),
                items=list(rows),
                provenance=[
                    SourceProvenance(
                        provider="marketstack",
                        domain="bars",
                        endpoint=(
                            f"/{version}/intraday"
                        ),
                        symbol=symbol.upper(),
                        metadata={
                            "interval": interval,
                        },
                    )
                ],
            ).finish()

        except Exception as exc:
            last_error = exc

    return _error(
        "marketstack",
        "bars",
        last_error
        or RuntimeError(
            "marketstack failed"
        ),
    )


def alphavantage_news(
    symbol: str,
) -> SourceResult:
    key = secret(
        "ALPHAVANTAGE_API_KEY"
    )

    if not key:
        return _unconfigured(
            "alphavantage",
            "news",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://www.alphavantage.co/query",
                params={
                    "function": "NEWS_SENTIMENT",
                    "tickers": symbol.upper(),
                    "sort": "LATEST",
                    "limit": 100,
                    "apikey": key,
                },
            )

        rows = (
            payload.get(
                "feed",
                [],
            )
            if isinstance(
                payload,
                dict,
            )
            else []
        )

        items = []

        for row in rows:
            title = str(
                row.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:
                continue

            url = str(
                row.get(
                    "url",
                    "",
                )
            )

            ticker_sentiment = (
                row.get(
                    "ticker_sentiment",
                    []
                )
                or []
            )

            symbol_sentiment = None

            for value in ticker_sentiment:
                if (
                    str(
                        value.get(
                            "ticker",
                            "",
                        )
                    ).upper()
                    ==
                    symbol.upper()
                ):
                    try:
                        symbol_sentiment = float(
                            value.get(
                                "ticker_sentiment_score"
                            )
                        )
                    except Exception:
                        pass

            item = RawNewsItem(
                provider="alphavantage",
                provider_id=_news_id(
                    "alphavantage",
                    title,
                    url,
                ),
                published_at=_timestamp(
                    row.get(
                        "time_published"
                    )
                ),
                title=title,
                url=url,
                summary=str(
                    row.get(
                        "summary",
                        "",
                    )
                ),
                source_name=str(
                    row.get(
                        "source",
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
                categories=tuple(
                    str(
                        topic.get(
                            "topic",
                            "",
                        )
                    )
                    for topic
                    in (
                        row.get(
                            "topics",
                            []
                        )
                        or []
                    )
                ),
                provider_sentiment=(
                    symbol_sentiment
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="alphavantage",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "alphavantage",
            "news",
            exc,
        )


def marketaux_news(
    symbol: str,
) -> SourceResult:
    key = secret(
        "MARKETAUX_API_TOKEN"
    )

    if not key:
        return _unconfigured(
            "marketaux",
            "news",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://api.marketaux.com/v1/news/all",
                params={
                    "api_token": key,
                    "symbols": symbol.upper(),
                    "filter_entities": "true",
                    "language": "en",
                    "limit": 50,
                },
            )

        rows = (
            payload.get(
                "data",
                [],
            )
            if isinstance(
                payload,
                dict,
            )
            else []
        )

        items = []

        for row in rows:
            title = str(
                row.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:
                continue

            url = str(
                row.get(
                    "url",
                    "",
                )
            )

            entities = (
                row.get(
                    "entities",
                    []
                )
                or []
            )

            entity_sentiment = None

            for entity in entities:
                if (
                    str(
                        entity.get(
                            "symbol",
                            "",
                        )
                    ).upper()
                    ==
                    symbol.upper()
                ):
                    try:
                        entity_sentiment = float(
                            entity.get(
                                "sentiment_score"
                            )
                        )
                    except Exception:
                        pass

            item = RawNewsItem(
                provider="marketaux",
                provider_id=str(
                    row.get(
                        "uuid"
                    )
                    or _news_id(
                        "marketaux",
                        title,
                        url,
                    )
                ),
                published_at=_timestamp(
                    row.get(
                        "published_at"
                    )
                ),
                title=title,
                url=url,
                summary=str(
                    row.get(
                        "description"
                    )
                    or row.get(
                        "snippet",
                        "",
                    )
                ),
                source_name=str(
                    row.get(
                        "source",
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
                provider_sentiment=(
                    entity_sentiment
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="marketaux",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "marketaux",
            "news",
            exc,
        )


def currents_news(
    symbol: str,
) -> SourceResult:
    key = secret(
        "CURRENT_NEWS_API_KEY"
    )

    if not key:
        return _unconfigured(
            "currents",
            "news",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                "https://api.currentsapi.services/v2/search",
                params={
                    "keywords": symbol.upper(),
                    "language": "en",
                    "page_size": 50,
                },
                headers={
                    "Authorization": (
                        f"Bearer {key}"
                    ),
                },
            )

        rows = (
            payload.get(
                "news",
                [],
            )
            if isinstance(
                payload,
                dict,
            )
            else []
        )

        items = []

        for row in rows:
            title = str(
                row.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:
                continue

            url = str(
                row.get(
                    "url",
                    "",
                )
            )

            item = RawNewsItem(
                provider="currents",
                provider_id=str(
                    row.get(
                        "id"
                    )
                    or _news_id(
                        "currents",
                        title,
                        url,
                    )
                ),
                published_at=_timestamp(
                    row.get(
                        "published"
                    )
                ),
                title=title,
                url=url,
                summary=str(
                    row.get(
                        "description",
                        "",
                    )
                ),
                source_name=str(
                    row.get(
                        "author",
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
                categories=tuple(
                    row.get(
                        "category",
                        [],
                    )
                    or []
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="currents",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "currents",
            "news",
            exc,
        )


def fmp_bundle(
    symbol: str,
) -> SourceResult:
    key = secret(
        "FMP_API_KEY"
    )

    if not key:
        return _unconfigured(
            "fmp",
            "fundamentals",
        )

    endpoints = (
        "profile",
        "key-metrics",
        "ratios",
        "income-statement",
        "balance-sheet-statement",
        "cash-flow-statement",
    )

    items = []

    try:
        with ProviderHTTPClient() as client:
            for endpoint in endpoints:
                payload = client.get_json(
                    (
                        "https://financialmodelingprep.com/"
                        f"stable/{endpoint}"
                    ),
                    params={
                        "symbol": symbol.upper(),
                        "apikey": key,
                    },
                )

                items.append(
                    {
                        "section": endpoint,
                        "data": payload,
                    }
                )

        return SourceResult(
            provider="fmp",
            domain="fundamentals",
            state=SourceState.OK,
            items=items,
            provenance=[
                SourceProvenance(
                    provider="fmp",
                    domain="fundamentals",
                    endpoint="/stable/*",
                    symbol=symbol.upper(),
                )
            ],
        ).finish()

    except Exception as exc:
        return _error(
            "fmp",
            "fundamentals",
            exc,
        )


def fmp_news(
    symbol: str,
) -> SourceResult:
    key = secret(
        "FMP_API_KEY"
    )

    if not key:
        return _unconfigured(
            "fmp",
            "news",
        )

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                (
                    "https://financialmodelingprep.com/"
                    "stable/news/stock"
                ),
                params={
                    "symbols": symbol.upper(),
                    "apikey": key,
                },
            )

        rows = (
            payload
            if isinstance(
                payload,
                list,
            )
            else []
        )

        items = []

        for row in rows:
            title = str(
                row.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:
                continue

            url = str(
                row.get(
                    "url",
                    "",
                )
            )

            item = RawNewsItem(
                provider="fmp",
                provider_id=_news_id(
                    "fmp",
                    title,
                    url,
                ),
                published_at=_timestamp(
                    row.get(
                        "publishedDate"
                    )
                    or row.get(
                        "publishedAt"
                    )
                ),
                title=title,
                url=url,
                summary=str(
                    row.get(
                        "text"
                    )
                    or row.get(
                        "snippet",
                        "",
                    )
                ),
                source_name=str(
                    row.get(
                        "site",
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="fmp",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "fmp",
            "news",
            exc,
        )


def openfigi_mapping(
    symbol: str,
    *,
    exchange_code: str = "US",
) -> SourceResult:
    key = secret(
        "OPENFIGI_API_KEY"
    )

    headers = {
        "Content-Type": (
            "application/json"
        ),
    }

    if key:
        headers[
            "X-OPENFIGI-APIKEY"
        ] = key

    try:
        with ProviderHTTPClient() as client:
            payload = client.post_json(
                "https://api.openfigi.com/v3/mapping",
                payload=[
                    {
                        "idType": "TICKER",
                        "idValue": symbol.upper(),
                        "exchCode": exchange_code,
                    }
                ],
                headers=headers,
            )

        rows = []

        if (
            isinstance(
                payload,
                list,
            )
            and payload
        ):
            first = payload[0]

            if isinstance(
                first,
                dict,
            ):
                rows = list(
                    first.get(
                        "data",
                        []
                    )
                    or []
                )

                warning = first.get(
                    "warning"
                )

                if warning:
                    return SourceResult(
                        provider="openfigi",
                        domain="symbol_mapping",
                        state=SourceState.EMPTY,
                        warnings=[
                            str(warning)
                        ],
                    ).finish()

        return SourceResult(
            provider="openfigi",
            domain="symbol_mapping",
            state=(
                SourceState.OK
                if rows
                else SourceState.EMPTY
            ),
            items=rows,
        ).finish()

    except Exception as exc:
        return _error(
            "openfigi",
            "symbol_mapping",
            exc,
        )


def thetadata_expirations(
    symbol: str,
) -> SourceResult:
    base = os.environ.get(
        "THETADATA_BASE_URL",
        "http://127.0.0.1:25503/v3",
    ).rstrip("/")

    try:
        with ProviderHTTPClient(
            timeout=5.0
        ) as client:
            payload = client.get_json(
                (
                    f"{base}/option/"
                    "list/expirations"
                ),
                params={
                    "symbol": symbol.upper(),
                    "format": "json",
                },
            )

        rows = (
            payload
            if isinstance(
                payload,
                list,
            )
            else (
                payload.get(
                    "response",
                    []
                )
                if isinstance(
                    payload,
                    dict,
                )
                else []
            )
        )

        return SourceResult(
            provider="thetadata",
            domain="options",
            state=(
                SourceState.OK
                if rows
                else SourceState.EMPTY
            ),
            items=list(rows),
            provenance=[
                SourceProvenance(
                    provider="thetadata",
                    domain="options",
                    endpoint=(
                        "/v3/option/list/"
                        "expirations"
                    ),
                    symbol=symbol.upper(),
                )
            ],
        ).finish()

    except Exception as exc:
        result = _error(
            "thetadata",
            "options",
            exc,
        )

        result.warnings.append(
            "ThetaData v3 requires the local Theta Terminal"
        )

        return result


def yahoo_snapshot(
    symbol: str,
) -> SourceResult:
    try:
        ticker = yf.Ticker(
            symbol.upper()
        )

        history = ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
        )

        if history.empty:
            return SourceResult(
                provider="yfinance",
                domain="bars",
                state=SourceState.EMPTY,
            ).finish()

        row = history.iloc[-1]

        item = {
            "timestamp": str(
                history.index[-1]
            ),
            "open": float(
                row["Open"]
            ),
            "high": float(
                row["High"]
            ),
            "low": float(
                row["Low"]
            ),
            "close": float(
                row["Close"]
            ),
            "volume": float(
                row["Volume"]
            ),
        }

        return SourceResult(
            provider="yfinance",
            domain="bars",
            state=SourceState.OK,
            items=[
                item
            ],
        ).finish()

    except Exception as exc:
        return _error(
            "yfinance",
            "bars",
            exc,
        )


def yahoo_fundamentals(
    symbol: str,
) -> SourceResult:
    try:
        ticker = yf.Ticker(
            symbol.upper()
        )

        info = ticker.get_info()

        return SourceResult(
            provider="yfinance",
            domain="fundamentals",
            state=(
                SourceState.OK
                if info
                else SourceState.EMPTY
            ),
            items=[
                info
            ] if info else [],
        ).finish()

    except Exception as exc:
        return _error(
            "yfinance",
            "fundamentals",
            exc,
        )


def yahoo_options(
    symbol: str,
) -> SourceResult:
    try:
        ticker = yf.Ticker(
            symbol.upper()
        )

        expirations = tuple(
            ticker.options or ()
        )

        items = []

        for expiration in expirations[:3]:
            chain = ticker.option_chain(
                expiration
            )

            items.append(
                {
                    "expiration": expiration,
                    "calls": (
                        chain.calls
                        .head(100)
                        .to_dict(
                            orient="records"
                        )
                    ),
                    "puts": (
                        chain.puts
                        .head(100)
                        .to_dict(
                            orient="records"
                        )
                    ),
                }
            )

        return SourceResult(
            provider="yfinance",
            domain="options",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "yfinance",
            "options",
            exc,
        )


def yahoo_news(
    symbol: str,
) -> SourceResult:
    try:
        ticker = yf.Ticker(
            symbol.upper()
        )

        rows = ticker.news or []

        items = []

        for raw in rows:
            content = (
                raw.get(
                    "content",
                    raw,
                )
                if isinstance(
                    raw,
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

            canonical = content.get(
                "canonicalUrl",
                {}
            )

            url = (
                str(
                    canonical.get(
                        "url",
                        "",
                    )
                )
                if isinstance(
                    canonical,
                    dict,
                )
                else str(
                    canonical or ""
                )
            )

            item = RawNewsItem(
                provider="yfinance",
                provider_id=_news_id(
                    "yfinance",
                    title,
                    url,
                ),
                published_at=_timestamp(
                    content.get(
                        "pubDate"
                    )
                    or raw.get(
                        "providerPublishTime"
                    )
                ),
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
                        "",
                    )
                ),
                symbols=(
                    symbol.upper(),
                ),
            )

            items.append(
                item.to_dict()
            )

        return SourceResult(
            provider="yfinance",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "yfinance",
            "news",
            exc,
        )


def rss_news(
    project_root: str | Path,
) -> SourceResult:
    config_path = (
        Path(project_root)
        / "config"
        / "rss_feeds.json"
    )

    if not config_path.is_file():
        return SourceResult(
            provider="rss",
            domain="news",
            state=SourceState.EMPTY,
            warnings=[
                "rss config missing"
            ],
        ).finish()

    import json

    config = json.loads(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    items = []
    warnings = []

    for feed in config.get(
        "feeds",
        [],
    ):
        if not feed.get(
            "enabled",
            True,
        ):
            continue

        try:
            rows = fetch_feed(
                str(
                    feed[
                        "url"
                    ]
                ),
                source_name=str(
                    feed[
                        "name"
                    ]
                ),
            )

            items.extend(
                row.to_dict()
                for row in rows
            )

        except Exception as exc:
            warnings.append(
                (
                    f"{feed.get('name')}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )
            )

    state = (
        SourceState.OK
        if items
        else (
            SourceState.PARTIAL
            if warnings
            else SourceState.EMPTY
        )
    )

    return SourceResult(
        provider="rss",
        domain="news",
        state=state,
        items=items,
        warnings=warnings,
    ).finish()


def eodhd_news(
    symbol: str,
    *,
    lookback_days: int = 7,
) -> SourceResult:
    key = secret(
        "EODHD_API_KEY"
    )

    if not key:
        return _unconfigured(
            "eodhd",
            "news",
        )

    try:
        from stocks.intelligence_agent.providers.eodhd import (
            EODHDProvider,
        )

        provider = EODHDProvider(
            key
        )

        end = _now().date()

        start = (
            end
            - timedelta(
                days=lookback_days
            )
        )

        provider_symbol = (
            symbol.upper()
            if "." in symbol
            else f"{symbol.upper()}.US"
        )

        try:
            rows = provider.fetch_news(
                symbol=provider_symbol,
                from_date=start.isoformat(),
                to_date=end.isoformat(),
                limit=100,
            )
        finally:
            provider.close()

        items = [
            {
                "article_id": row.article_id,
                "published_at": (
                    row.published_at.isoformat()
                ),
                "title": row.title,
                "summary": row.body,
                "url": row.url,
                "source": row.source,
                "symbols": list(
                    row.symbols
                ),
                "tags": list(
                    row.tags
                ),
            }
            for row in rows
        ]

        return SourceResult(
            provider="eodhd",
            domain="news",
            state=(
                SourceState.OK
                if items
                else SourceState.EMPTY
            ),
            items=items,
        ).finish()

    except Exception as exc:
        return _error(
            "eodhd",
            "news",
            exc,
        )
