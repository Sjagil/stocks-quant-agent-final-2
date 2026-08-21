from __future__ import annotations

import json
from urllib.parse import unquote
from pathlib import Path

from stocks.providers.federation_v2_27 import (
    REDACTED,
    assert_payload_contains_no_secrets,
    sanitize_payload,
    write_json,
)


def test_ibkr_host_and_port_are_not_treated_as_secrets(
    monkeypatch,
):
    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "7496")
    payload = {
        "host": "127.0.0.1",
        "port": "7496",
        "rows": 7496,
    }
    safe, audit = sanitize_payload(payload)
    assert safe == payload
    assert audit["redaction_count"] == 0


def test_real_configured_api_key_is_redacted_everywhere(
    monkeypatch,
):
    secret = "fred-secret-1234567890"
    monkeypatch.setenv("FRED_API_KEY", secret)
    payload = {
        "normal": f"prefix-{secret}-suffix",
        "api_key": secret,
        "url": (
            "https://example.test/path?"
            f"api_key={secret}&symbol=AAPL"
        ),
    }
    safe, audit = sanitize_payload(payload)
    encoded = json.dumps(safe)
    assert secret not in encoded
    assert safe["api_key"] == REDACTED
    assert REDACTED in safe["normal"]
    assert REDACTED in unquote(safe["url"])
    assert audit["redaction_count"] >= 3
    assert_payload_contains_no_secrets(safe)


def test_short_secret_is_redacted_when_structurally_labeled(
    monkeypatch,
):
    monkeypatch.setenv("Nasdaq_API_KEY", "9")
    safe, _ = sanitize_payload(
        {"api_key": "9", "market_value": 9}
    )
    assert safe["api_key"] == REDACTED
    assert safe["market_value"] == 9


def test_write_json_never_persists_raw_secret(
    tmp_path: Path,
    monkeypatch,
):
    secret = "polygon-secret-abcdef"
    monkeypatch.setenv("POLYGON_API_KEY", secret)
    target = tmp_path / "audit.json"
    write_json(
        target,
        {
            "provider": "polygon",
            "error": f"request failed {secret}",
        },
    )
    text = target.read_text(encoding="utf-8")
    assert secret not in text
    assert REDACTED in text


def test_url_bearer_and_query_tokens_are_redacted_without_env():
    safe, audit = sanitize_payload(
        {
            "authorization": "Bearer abcdefghijk",
            "url": (
                "https://example.test/x?"
                "token=abcdefghijk&symbol=AAPL"
            ),
        }
    )
    encoded = json.dumps(safe)
    assert "abcdefghijk" not in encoded
    assert audit["redaction_count"] >= 2
