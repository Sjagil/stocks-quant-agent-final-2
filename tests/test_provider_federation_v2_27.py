from __future__ import annotations

import json

from stocks.providers.federation_v2_27 import (
    assert_payload_contains_no_secrets,
    extract_news_items,
    normalize_symbols,
    summarize_source_fabric,
)


def test_symbol_normalization_is_stable_and_bounded():
    assert normalize_symbols([" aapl ", "AAPL", "msft", ""], limit=2) == ["AAPL", "MSFT"]


def test_news_extraction_deduplicates_and_preserves_query_symbol():
    payload = {
        "symbols": {
            "AAPL": {
                "results": [
                    {
                        "provider": "finnhub",
                        "domain": "news",
                        "state": "OK",
                        "items": [
                            {"provider_id": "1", "title": "Apple event", "url": "https://example.test/a"},
                            {"provider_id": "1", "title": "Apple event", "url": "https://example.test/a"},
                        ],
                    }
                ]
            }
        }
    }
    rows = extract_news_items(payload)
    assert len(rows) == 1
    assert rows[0]["query_symbol"] == "AAPL"
    assert rows[0]["provider"] == "finnhub"


def test_source_summary_counts_global_and_symbol_results():
    payload = {
        "symbols": {
            "AAPL": {
                "results": [
                    {"provider": "polygon", "domain": "live_quotes", "state": "OK"},
                    {"provider": "fmp", "domain": "fundamentals", "state": "UNCONFIGURED"},
                ]
            }
        },
        "global": {"results": [{"provider": "openexchangerates", "domain": "fx", "state": "OK"}]},
    }
    summary = summarize_source_fabric(payload)
    assert summary["providers"]["polygon"]["OK"] == 1
    assert summary["providers"]["openexchangerates"]["OK"] == 1


def test_secret_leak_guard_blocks_configured_value(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "super-secret-test-value")
    try:
        assert_payload_contains_no_secrets({"safe": "value"})
    except Exception as exc:  # pragma: no cover
        raise AssertionError(exc)
    try:
        assert_payload_contains_no_secrets({"bad": "super-secret-test-value"})
    except RuntimeError as exc:
        assert "SECRET_VALUE_LEAK" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("secret leak guard did not block")
