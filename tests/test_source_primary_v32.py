from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from stocks.providers.catalog import SOURCES
from stocks.providers.http import (
    ProviderEntitlementError,
    ProviderHTTPClient,
)


def source(name: str):
    return next(item for item in SOURCES if item.name == name)


def test_paid_primary_sources_are_authoritative() -> None:
    assert source("eodhd").authoritative is True
    assert source("openexchangerates").authoritative is True


def test_http_errors_never_expose_query_secrets() -> None:
    request = httpx.Request(
        "GET",
        "https://example.com/data?api_key=SUPER_SECRET_VALUE",
    )

    response = httpx.Response(
        403,
        request=request,
    )

    with pytest.raises(ProviderEntitlementError) as exc:
        ProviderHTTPClient._validate(response)

    message = str(exc.value)

    assert "SUPER_SECRET_VALUE" not in message
    assert "api_key" not in message
    assert "?" not in message


def test_eodhd_news_maps_body_and_url(monkeypatch) -> None:
    import stocks.intelligence_agent.providers.eodhd as module
    from stocks.providers.adapters import eodhd_news

    class FakeProvider:
        def __init__(self, api_key: str):
            assert api_key

        def close(self) -> None:
            pass

        def fetch_news(self, **kwargs):
            return [
                SimpleNamespace(
                    article_id="TEST-1",
                    published_at=datetime(
                        2026,
                        8,
                        13,
                        tzinfo=timezone.utc,
                    ),
                    title="Example earnings story",
                    body="Full provider body",
                    source="EODHD",
                    symbols=("AAPL.US",),
                    tags=("earnings",),
                    url="https://example.com/story",
                )
            ]

    monkeypatch.setenv(
        "EODHD_API_KEY",
        "test-only-key",
    )

    monkeypatch.setattr(
        module,
        "EODHDProvider",
        FakeProvider,
    )

    result = eodhd_news("AAPL")

    assert str(result.state) == "OK"
    assert len(result.items) == 1
    assert result.items[0]["summary"] == "Full provider body"
    assert result.items[0]["url"] == "https://example.com/story"
