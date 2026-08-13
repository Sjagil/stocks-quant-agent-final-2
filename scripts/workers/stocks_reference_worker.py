from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _common import (
    add_repo_src,
    artifact_ref,
    base_health,
    repo_catalog,
    run_worker,
)


CAPABILITIES = (
    "health",
    "catalog",
    "news_link",
)


def _repo(
    request: dict,
) -> Path:
    value = (
        request.get(
            "context"
        )
        or {}
    ).get(
        "repo_path"
    )

    if not value:
        raise ValueError(
            "reference repo_path missing"
        )

    path = Path(
        value
    ).resolve()

    if not path.is_dir():
        raise FileNotFoundError(
            path
        )

    return path


def _health(
    request: dict,
) -> dict:
    repo = _repo(
        request
    )

    add_repo_src(
        repo
    )

    return base_health(
        request,
        distributions=(),
        imports=(
            "stocks.news.intelligence",
            "stocks.screener.service",
            "stocks.research.sec_overlay",
            "stocks.microstructure.orderflow",
        ),
        capabilities=(
            CAPABILITIES
        ),
    )


def _catalog(
    request: dict,
) -> dict:
    repo = _repo(
        request
    )

    return {
        "state": "OK",
        "data": {
            "purpose": (
                "Production donor for PIT screener, "
                "news intelligence, SEC and orderflow."
            ),
            "repo_catalog": repo_catalog(
                repo,
                (
                    "src/stocks/news/*.py",
                    "src/stocks/screener/*.py",
                    "src/stocks/research/sec_overlay.py",
                    "src/stocks/microstructure/orderflow.py",
                ),
            ),
        },
    }


def _normalize_symbol(
    value: Any,
) -> str:
    text = str(
        value
        or ""
    ).strip().upper()

    if "." in text:
        text = text.split(
            ".",
            1,
        )[0]

    return text


def _news_link(
    request: dict,
    artifact_dir: Path,
) -> dict:
    repo = _repo(
        request
    )

    add_repo_src(
        repo
    )

    from stocks.news import (
        intelligence,
    )

    payload = dict(
        request.get(
            "payload"
        )
        or {}
    )

    raw_universe = dict(
        payload.get(
            "universe"
        )
        or {}
    )

    universe: dict[
        str,
        dict[str, str],
    ] = {}

    for raw_symbol, metadata in (
        raw_universe.items()
    ):
        symbol = _normalize_symbol(
            raw_symbol
        )

        if not symbol:
            continue

        metadata = dict(
            metadata
            or {}
        )

        universe[
            symbol
        ] = {
            "name": str(
                metadata.get(
                    "name",
                    "",
                )
            ),
            "sector": str(
                metadata.get(
                    "sector",
                    "",
                )
            ),
            "industry": str(
                metadata.get(
                    "industry",
                    "",
                )
            ),
            "underlying_commodity": str(
                metadata.get(
                    "underlying_commodity",
                    "",
                )
            ),
        }

    config_path = (
        repo
        / "config"
        / "news"
        / "event_intelligence_v1.json"
    )

    config = json.loads(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    alias_index = (
        intelligence
        ._company_alias_index(
            universe
        )
    )

    records = []

    for raw in list(
        payload.get(
            "items"
        )
        or []
    ):
        if not isinstance(
            raw,
            dict,
        ):
            continue

        title = " ".join(
            str(
                raw.get(
                    "title"
                )
                or ""
            ).split()
        )

        if not title:
            continue

        direct_symbols = {
            symbol
            for value in (
                raw.get(
                    "symbols"
                )
                or []
            )
            if (
                symbol := (
                    _normalize_symbol(
                        value
                    )
                )
            )
            in universe
        }

        linked = (
            direct_symbols
            |
            intelligence._link_symbols(
                title,
                universe=universe,
                alias_index=alias_index,
            )
        )

        symbols = tuple(
            sorted(
                linked
            )
        )

        sectors = tuple(
            sorted(
                {
                    universe[
                        symbol
                    ].get(
                        "sector",
                        "",
                    )
                    for symbol
                    in symbols
                    if universe[
                        symbol
                    ].get(
                        "sector"
                    )
                }
            )
        )

        industries = tuple(
            sorted(
                {
                    universe[
                        symbol
                    ].get(
                        "industry",
                        "",
                    )
                    for symbol
                    in symbols
                    if universe[
                        symbol
                    ].get(
                        "industry"
                    )
                }
            )
        )

        normalized = (
            intelligence
            ._normalized_title(
                title
            )
        )

        commodities = tuple(
            sorted(
                {
                    commodity
                    for term, commodity
                    in intelligence
                    .COMMODITY_TERMS
                    .items()
                    if term in normalized
                }
            )
        )

        classes = (
            intelligence
            ._event_classes(
                normalized,
                config,
            )
        )

        (
            sentiment,
            sentiment_method,
            sentiment_confidence,
        ) = intelligence._sentiment(
            normalized,
            raw.get(
                "sentiment_polarity"
            ),
            classes,
        )

        relevance = (
            intelligence
            ._relevance(
                symbols,
                sectors,
                commodities,
            )
        )

        severity = (
            intelligence
            ._severity(
                normalized,
                classes,
                config,
            )
        )

        source = str(
            raw.get(
                "source"
            )
            or raw.get(
                "provider"
            )
            or "UNKNOWN"
        )

        source_class = (
            intelligence
            ._source_class(
                source
            )
        )

        source_quality = (
            intelligence
            ._source_quality(
                source,
                source_class,
                config,
            )
        )

        records.append(
            {
                "provider_id": (
                    raw.get(
                        "provider_id"
                    )
                    or raw.get(
                        "article_id"
                    )
                ),
                "published_at": (
                    raw.get(
                        "published_at"
                    )
                ),
                "title": title,
                "source": source,
                "source_class": (
                    source_class
                ),
                "direct_symbols": sorted(
                    direct_symbols
                ),
                "linked_symbols": list(
                    symbols
                ),
                "sectors": list(
                    sectors
                ),
                "industries": list(
                    industries
                ),
                "commodities": list(
                    commodities
                ),
                "event_classes": list(
                    classes
                ),
                "sentiment": float(
                    sentiment
                ),
                "sentiment_method": (
                    sentiment_method
                ),
                "sentiment_confidence": float(
                    sentiment_confidence
                ),
                "relevance": float(
                    relevance
                ),
                "severity": float(
                    severity
                ),
                "source_quality": float(
                    source_quality
                ),
                "entity_linking_method": (
                    "STOCKS_REFERENCE_"
                    "PROVIDER_SYMBOL_PLUS_"
                    "SECURITY_MASTER_ALIAS_V1"
                ),
                "execution_authority": (
                    "NONE"
                ),
            }
        )

    output = (
        artifact_dir
        / "stocks_news_link.json"
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "stocks_reference_"
                    "news_link_v1"
                ),
                "article_count": len(
                    records
                ),
                "linked_article_count": sum(
                    bool(
                        row[
                            "linked_symbols"
                        ]
                    )
                    for row in records
                ),
                "rows": records,
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "state": "OK",
        "data": {
            "article_count": len(
                records
            ),
            "linked_article_count": sum(
                bool(
                    row[
                        "linked_symbols"
                    ]
                )
                for row in records
            ),
            "execution_authority": (
                "NONE"
            ),
        },
        "artifacts": [
            artifact_ref(
                output,
                media_type=(
                    "application/json"
                ),
                rows=len(
                    records
                ),
            )
        ],
    }


def handle(
    request: dict,
    artifact_dir: Path,
) -> dict:
    action = request[
        "action"
    ]

    if action == "health":
        return _health(
            request
        )

    if action == "catalog":
        return _catalog(
            request
        )

    if action == "news_link":
        return _news_link(
            request,
            artifact_dir,
        )

    raise ValueError(
        f"unsupported stocks_reference "
        f"action: {action}"
    )


if __name__ == "__main__":
    run_worker(
        handle
    )
