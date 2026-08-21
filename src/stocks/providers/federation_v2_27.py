from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from stocks.providers.catalog import SOURCES


SCHEMA = "provider_federation_v2_27_1"


def normalize_symbols(values: Iterable[Any], *, limit: int | None = None) -> list[str]:
    result: list[str] = []
    for value in values:
        symbol = str(value or "").strip().upper()
        if not symbol or symbol in result:
            continue
        result.append(symbol)
        if limit is not None and len(result) >= int(limit):
            break
    return result


def symbols_from_csv(path: str | Path, *, limit: int = 12) -> list[str]:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    frame = pd.read_csv(target)
    if "symbol" not in frame.columns:
        raise ValueError(f"symbol column missing from {target}")
    return normalize_symbols(frame["symbol"].tolist(), limit=limit)


def provider_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        rows.append(
            {
                "provider": source.name,
                "domains": [str(value) for value in source.domains],
                "configured": bool(source.configured()),
                "research": bool(source.research),
                "live_context": bool(source.live_context),
                "authoritative": bool(source.authoritative),
                "requires_key": bool(source.requires_key),
                "notes": source.notes,
            }
        )
    return rows


def summarize_source_fabric(payload: Mapping[str, Any]) -> dict[str, Any]:
    provider_states: dict[str, Counter[str]] = {}
    domain_states: dict[str, Counter[str]] = {}
    for symbol_payload in (payload.get("symbols") or {}).values():
        for result in (symbol_payload.get("results") or []):
            provider = str(result.get("provider") or "UNKNOWN")
            domain = str(result.get("domain") or "UNKNOWN")
            state = str(result.get("state") or "UNKNOWN")
            provider_states.setdefault(provider, Counter())[state] += 1
            domain_states.setdefault(domain, Counter())[state] += 1
    for result in (payload.get("global") or {}).get("results") or []:
        provider = str(result.get("provider") or "UNKNOWN")
        domain = str(result.get("domain") or "UNKNOWN")
        state = str(result.get("state") or "UNKNOWN")
        provider_states.setdefault(provider, Counter())[state] += 1
        domain_states.setdefault(domain, Counter())[state] += 1
    return {
        "providers": {name: dict(counter) for name, counter in sorted(provider_states.items())},
        "domains": {name: dict(counter) for name, counter in sorted(domain_states.items())},
    }


def extract_news_items(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for symbol, symbol_payload in (payload.get("symbols") or {}).items():
        for result in symbol_payload.get("results") or []:
            if str(result.get("domain")) != "news":
                continue
            provider = str(result.get("provider") or "UNKNOWN")
            for raw in result.get("items") or []:
                if not isinstance(raw, dict):
                    continue
                row = dict(raw)
                title = str(row.get("title") or "").strip()
                url = str(row.get("url") or "").strip()
                provider_id = str(row.get("provider_id") or row.get("id") or "")
                key = (provider, provider_id, url or title)
                if key in seen:
                    continue
                seen.add(key)
                row.setdefault("provider", provider)
                row.setdefault("source", provider)
                row["query_symbol"] = str(symbol).upper()
                row.setdefault("provider_symbols", [str(symbol).upper()])
                items.append(row)
    return items


def universe_metadata(payload: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    universe: dict[str, dict[str, str]] = {}
    for symbol, symbol_payload in (payload.get("symbols") or {}).items():
        metadata = {"name": "", "sector": "", "industry": "", "underlying_commodity": ""}
        for result in symbol_payload.get("results") or []:
            if str(result.get("provider")) != "fmp" or str(result.get("domain")) != "fundamentals":
                continue
            for section in result.get("items") or []:
                if not isinstance(section, dict) or section.get("section") != "profile":
                    continue
                data = section.get("data") or []
                record = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
                if isinstance(record, dict):
                    metadata["name"] = str(record.get("companyName") or record.get("companyNameLong") or "")
                    metadata["sector"] = str(record.get("sector") or "")
                    metadata["industry"] = str(record.get("industry") or "")
        universe[str(symbol).upper()] = metadata
    return universe


def integration_summary(response: Any) -> dict[str, Any]:
    return {
        "state": str(getattr(getattr(response, "state", None), "value", getattr(response, "state", "UNKNOWN"))),
        "ok": bool(getattr(response, "ok", False)),
        "error": getattr(response, "error", None),
        "warnings": list(getattr(response, "warnings", ()) or ()),
        "data": dict(getattr(response, "data", {}) or {}),
        "artifacts": [str(getattr(item, "path", "")) for item in (getattr(response, "artifacts", ()) or ())],
    }


def configured_secret_values() -> tuple[str, ...]:
    names: set[str] = set()
    for source in SOURCES:
        names.update(source.env_any)
        names.update(source.env_all)
    names.update(
        {
            "CURRENT_NEWS_API_KEY",
            "THETA_DATA_API_KEY",
            "FRED_API_KEY",
            "FISCAL_API_KEY",
            "DUNE_API_KEY",
            "IBKR_ACCOUNT_FINGERPRINT_KEY",
        }
    )
    values = []
    for name in names:
        value = os.environ.get(name, "").strip()
        if value and len(value) >= 4:
            values.append(value)
    return tuple(sorted(set(values), key=len, reverse=True))


def assert_payload_contains_no_secrets(payload: Mapping[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True, default=str)
    for value in configured_secret_values():
        if value in encoded:
            raise RuntimeError("SECRET_VALUE_LEAK_DETECTED_IN_FEDERATION_ARTIFACT")


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    assert_payload_contains_no_secrets(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return target
