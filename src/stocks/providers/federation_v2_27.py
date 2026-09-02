from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

from stocks.providers.catalog import SOURCES


SCHEMA = "provider_federation_v2_27_3"

# Only values that are actually credentials belong here.  Hostnames, ports,
# feature flags, provider names and other ordinary configuration are excluded.
SECRET_ENV_NAMES = frozenset(
    {
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
        "CURRENT_NEWS_API_KEY",
        "THETA_DATA_API_KEY",
        "OPENEXCHANGERATES_APP_ID",
        "OPENEXCHANGE_API_KEY",
        "FRED_API_KEY",
        "FISCAL_API_KEY",
        "TWELVEDATA_API_KEY",
        "MARKETSTACK_API_KEY",
        "FMP_API_KEY",
        "COINPAPRIKA_API_KEY",
        "ALPHAVANTAGE_API_KEY",
        "MARKETAUX_API_TOKEN",
        "OPENFIGI_API_KEY",
        "Nasdaq_API_KEY",
        "NASDAQ_API_KEY",
        "POLYGON_API_KEY",
        "FINNHUB_API_KEY",
        "DUNE_API_KEY",
        "CURRENCYLAYER_API_KEY",
        "CURRENCYLAYER_ACCESS_KEY",
        "IBKR_ACCOUNT_FINGERPRINT_KEY",
    }
)

REDACTED = "[REDACTED]"
_URL_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "api_token",
        "token",
        "access_token",
        "access_key",
        "app_id",
        "authorization",
        "password",
        "secret",
        "client_secret",
    }
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{6,}")


def normalize_symbols(
    values: Iterable[Any],
    *,
    limit: int | None = None,
) -> list[str]:
    result: list[str] = []
    for value in values:
        symbol = str(value or "").strip().upper()
        if not symbol or symbol in result:
            continue
        result.append(symbol)
        if limit is not None and len(result) >= int(limit):
            break
    return result


def symbols_from_csv(
    path: str | Path,
    *,
    limit: int = 12,
) -> list[str]:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    frame = pd.read_csv(target)
    if "symbol" not in frame.columns:
        raise ValueError(
            f"symbol column missing from {target}"
        )
    return normalize_symbols(
        frame["symbol"].tolist(),
        limit=limit,
    )


def provider_inventory() -> list[dict[str, Any]]:
    return [
        {
            "provider": source.name,
            "domains": [
                str(value)
                for value in source.domains
            ],
            "configured": bool(source.configured()),
            "research": bool(source.research),
            "live_context": bool(source.live_context),
            "authoritative": bool(source.authoritative),
            "requires_key": bool(source.requires_key),
            "notes": source.notes,
        }
        for source in SOURCES
    ]


def summarize_source_fabric(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    provider_states: dict[
        str, Counter[str]
    ] = {}
    domain_states: dict[
        str, Counter[str]
    ] = {}

    def consume(result: Mapping[str, Any]) -> None:
        provider = str(
            result.get("provider") or "UNKNOWN"
        )
        domain = str(
            result.get("domain") or "UNKNOWN"
        )
        state = str(
            result.get("state") or "UNKNOWN"
        )
        provider_states.setdefault(
            provider,
            Counter(),
        )[state] += 1
        domain_states.setdefault(
            domain,
            Counter(),
        )[state] += 1

    for symbol_payload in (
        payload.get("symbols") or {}
    ).values():
        for result in (
            symbol_payload.get("results") or []
        ):
            if isinstance(result, Mapping):
                consume(result)

    for result in (
        (payload.get("global") or {})
        .get("results")
        or []
    ):
        if isinstance(result, Mapping):
            consume(result)

    return {
        "providers": {
            name: dict(counter)
            for name, counter
            in sorted(provider_states.items())
        },
        "domains": {
            name: dict(counter)
            for name, counter
            in sorted(domain_states.items())
        },
    }


def extract_news_items(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for symbol, symbol_payload in (
        payload.get("symbols") or {}
    ).items():
        for result in (
            symbol_payload.get("results") or []
        ):
            if str(result.get("domain")) != "news":
                continue

            provider = str(
                result.get("provider") or "UNKNOWN"
            )

            for raw in result.get("items") or []:
                if not isinstance(raw, dict):
                    continue

                row = dict(raw)
                title = str(
                    row.get("title") or ""
                ).strip()
                url = str(
                    row.get("url") or ""
                ).strip()
                provider_id = str(
                    row.get("provider_id")
                    or row.get("id")
                    or ""
                )
                key = (
                    provider,
                    provider_id,
                    url or title,
                )
                if key in seen:
                    continue
                seen.add(key)

                row.setdefault(
                    "provider",
                    provider,
                )
                row.setdefault(
                    "source",
                    provider,
                )
                row["query_symbol"] = (
                    str(symbol).upper()
                )
                row.setdefault(
                    "provider_symbols",
                    [str(symbol).upper()],
                )
                items.append(row)

    return items


def universe_metadata(
    payload: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    universe: dict[
        str, dict[str, str]
    ] = {}

    for symbol, symbol_payload in (
        payload.get("symbols") or {}
    ).items():
        metadata = {
            "name": "",
            "sector": "",
            "industry": "",
            "underlying_commodity": "",
        }

        for result in (
            symbol_payload.get("results") or []
        ):
            if (
                str(result.get("provider")) != "fmp"
                or str(result.get("domain"))
                != "fundamentals"
            ):
                continue

            for section in (
                result.get("items") or []
            ):
                if (
                    not isinstance(section, dict)
                    or section.get("section")
                    != "profile"
                ):
                    continue

                data = section.get("data") or []
                if (
                    isinstance(data, list)
                    and data
                ):
                    record = data[0]
                elif isinstance(data, dict):
                    record = data
                else:
                    record = {}

                if isinstance(record, dict):
                    metadata["name"] = str(
                        record.get("companyName")
                        or record.get(
                            "companyNameLong"
                        )
                        or ""
                    )
                    metadata["sector"] = str(
                        record.get("sector") or ""
                    )
                    metadata["industry"] = str(
                        record.get("industry") or ""
                    )

        universe[str(symbol).upper()] = (
            metadata
        )

    return universe


def integration_summary(
    response: Any,
) -> dict[str, Any]:
    payload = {
        "state": str(
            getattr(
                getattr(
                    response,
                    "state",
                    None,
                ),
                "value",
                getattr(
                    response,
                    "state",
                    "UNKNOWN",
                ),
            )
        ),
        "ok": bool(
            getattr(response, "ok", False)
        ),
        "error": getattr(
            response,
            "error",
            None,
        ),
        "warnings": list(
            getattr(
                response,
                "warnings",
                (),
            )
            or ()
        ),
        "data": dict(
            getattr(
                response,
                "data",
                {},
            )
            or {}
        ),
        "artifacts": [
            str(getattr(item, "path", ""))
            for item in (
                getattr(
                    response,
                    "artifacts",
                    (),
                )
                or ()
            )
        ],
    }
    safe, _ = sanitize_payload(payload)
    return dict(safe)


def configured_secrets() -> dict[str, str]:
    result: dict[str, str] = {}
    for name in sorted(SECRET_ENV_NAMES):
        value = os.environ.get(
            name,
            "",
        ).strip()
        if value:
            result[name] = value
    return result


def _sensitive_mapping_key(
    value: Any,
) -> bool:
    key = str(value or "").strip().lower()
    if not key:
        return False
    if key in _URL_SECRET_KEYS:
        return True
    return any(
        key.endswith(suffix)
        for suffix in (
            "_api_key",
            "_api_token",
            "_access_key",
            "_access_token",
            "_app_id",
            "_password",
            "_secret",
            "_client_secret",
            "_authorization",
            "_fingerprint_key",
        )
    )


def _redact_url(value: str) -> tuple[str, bool]:
    try:
        parts = urlsplit(value)
    except Exception:
        return value, False

    if not parts.scheme or not parts.netloc:
        return value, False

    query = parse_qsl(
        parts.query,
        keep_blank_values=True,
    )
    if not query:
        return value, False

    changed = False
    safe_query = []
    for key, item in query:
        if _sensitive_mapping_key(key):
            safe_query.append((key, REDACTED))
            changed = True
        else:
            safe_query.append((key, item))

    if not changed:
        return value, False

    return (
        urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(safe_query),
                parts.fragment,
            )
        ),
        True,
    )


def _redact_string(
    value: str,
    *,
    secrets: Mapping[str, str],
    path: str,
    findings: list[dict[str, str]],
) -> str:
    result, url_changed = _redact_url(value)
    if url_changed:
        findings.append(
            {
                "path": path,
                "source": "URL_QUERY_SECRET",
                "fingerprint": "",
            }
        )

    bearer = _BEARER.sub(
        "Bearer " + REDACTED,
        result,
    )
    if bearer != result:
        findings.append(
            {
                "path": path,
                "source": "AUTHORIZATION_BEARER",
                "fingerprint": "",
            }
        )
        result = bearer

    # Global raw-value matching is only reliable for reasonably long
    # credentials. Short credentials are protected structurally by key/query
    # redaction; matching "9", "test", etc. against arbitrary market payloads
    # would create unavoidable false positives.
    for name, secret in secrets.items():
        if len(secret) < 8:
            continue
        if secret in result:
            result = result.replace(
                secret,
                REDACTED,
            )
            findings.append(
                {
                    "path": path,
                    "source": name,
                    "fingerprint": (
                        hashlib.sha256(
                            secret.encode("utf-8")
                        ).hexdigest()[:12]
                    ),
                }
            )

    return result


def sanitize_payload(
    payload: Any,
) -> tuple[Any, dict[str, Any]]:
    secrets = configured_secrets()
    findings: list[
        dict[str, str]
    ] = []

    def walk(
        value: Any,
        path: str,
    ) -> Any:
        if isinstance(value, Mapping):
            safe: dict[str, Any] = {}
            for raw_key, item in value.items():
                key = str(raw_key)
                child = f"{path}.{key}"

                if _sensitive_mapping_key(key):
                    if item not in (
                        None,
                        "",
                        REDACTED,
                    ):
                        findings.append(
                            {
                                "path": child,
                                "source": (
                                    "SENSITIVE_FIELD"
                                ),
                                "fingerprint": "",
                            }
                        )
                    safe[key] = (
                        None
                        if item is None
                        else REDACTED
                    )
                    continue

                safe[key] = walk(
                    item,
                    child,
                )
            return safe

        if isinstance(value, tuple):
            return [
                walk(item, f"{path}[{i}]")
                for i, item
                in enumerate(value)
            ]

        if isinstance(value, list):
            return [
                walk(item, f"{path}[{i}]")
                for i, item
                in enumerate(value)
            ]

        if isinstance(value, set):
            return [
                walk(item, f"{path}[{i}]")
                for i, item
                in enumerate(
                    sorted(value, key=str)
                )
            ]

        if isinstance(value, str):
            return _redact_string(
                value,
                secrets=secrets,
                path=path,
                findings=findings,
            )

        return value

    safe = walk(payload, "$")

    audit = {
        "schema": (
            "secret_redaction_audit_v2_27_3"
        ),
        "redaction_count": len(findings),
        "redacted_paths": findings,
        "configured_secret_names": sorted(
            secrets
        ),
        "short_secret_global_scan_skipped": sorted(
            name
            for name, value
            in secrets.items()
            if len(value) < 8
        ),
        "raw_secret_values_logged": False,
    }
    return safe, audit


def assert_payload_contains_no_secrets(
    payload: Any,
) -> None:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        default=str,
    )

    for name, secret in (
        configured_secrets().items()
    ):
        if (
            len(secret) >= 8
            and secret in encoded
        ):
            fingerprint = hashlib.sha256(
                secret.encode("utf-8")
            ).hexdigest()[:12]
            raise RuntimeError(
                "SECRET_VALUE_LEAK_DETECTED:"
                f"{name}:{fingerprint}"
            )


def sanitize_exception_text(
    exc: BaseException,
) -> str:
    raw = (
        f"{type(exc).__name__}: {exc}"
    )
    safe, _ = sanitize_payload(
        {"error": raw}
    )
    return str(
        safe.get("error")
        if isinstance(safe, Mapping)
        else "ERROR"
    )


def write_json(
    path: str | Path,
    payload: Mapping[str, Any],
) -> Path:
    safe, audit = sanitize_payload(
        payload
    )
    if isinstance(safe, dict):
        safe.setdefault(
            "secret_redaction_audit",
            audit,
        )

    assert_payload_contains_no_secrets(
        safe
    )

    target = Path(path)
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    target.write_text(
        json.dumps(
            safe,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    return target
