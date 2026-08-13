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
    "multitimeframe_collect",
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

        summary = " ".join(
            str(
                raw.get(
                    "summary"
                )
                or ""
            ).split()
        )

        provider_symbols = {
            symbol
            for value in (
                raw.get(
                    "provider_symbols"
                )
                or raw.get(
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

        combined_text = (
            title
            + " "
            + summary
        ).strip()

        text_linked_symbols = (
            intelligence._link_symbols(
                combined_text,
                universe=universe,
                alias_index=alias_index,
            )
        )

        validated_provider_symbols = (
            provider_symbols
            & text_linked_symbols
        )

        provider_only_symbols = (
            provider_symbols
            - text_linked_symbols
        )

        direct_symbols = (
            text_linked_symbols
        )

        linked = (
            text_linked_symbols
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
                "provider_symbols": sorted(
                    provider_symbols
                ),
                "validated_provider_symbols": sorted(
                    validated_provider_symbols
                ),
                "provider_only_symbols": sorted(
                    provider_only_symbols
                ),
                "query_symbol": str(
                    raw.get(
                        "query_symbol"
                    )
                    or ""
                ).upper(),
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



def _payload_list(
    payload: dict,
    key: str,
    default: tuple[str, ...],
) -> list[str]:
    value = payload.get(
        key,
        list(default),
    )

    if isinstance(value, str):
        values = value.split(",")
    else:
        values = list(value or default)

    return [
        str(item).strip()
        for item in values
        if str(item).strip()
    ]


def _partition_value(
    path: Path,
    prefix: str,
) -> str | None:
    for part in path.parts:
        if part.startswith(prefix):
            return part.split(
                "=",
                1,
            )[1]

    return None


def _multitimeframe_collect(
    request: dict,
    artifact_dir: Path,
) -> dict:
    repo = _repo(
        request
    )

    add_repo_src(
        repo
    )

    from stocks.data.multitimeframe import (
        audit_multitimeframe_sources,
        collect_multitimeframe_data,
        multitimeframe_status,
        provider_inventory,
        validate_multitimeframe_cache,
    )

    payload = dict(
        request.get(
            "payload"
        )
        or {}
    )

    symbols = [
        symbol.upper()
        for symbol in _payload_list(
            payload,
            "symbols",
            (
                "AAPL",
                "SPY",
            ),
        )
    ]

    intervals = [
        interval.lower()
        for interval in _payload_list(
            payload,
            "intervals",
            (
                "15m",
                "1h",
                "1d",
            ),
        )
    ]

    providers = [
        provider.lower()
        for provider in _payload_list(
            payload,
            "providers",
            (
                "eodhd",
                "yfinance",
            ),
        )
    ]

    allowed_intervals = {
        "15m",
        "1h",
        "1d",
    }

    unsupported_intervals = (
        set(intervals)
        - allowed_intervals
    )

    if unsupported_intervals:
        raise ValueError(
            "stocks_reference acquisition only accepts "
            "native 15m, 1h and 1d inputs; "
            "2h/4h/1w belong to the canonical main "
            "timeframe pipeline: "
            + ", ".join(
                sorted(
                    unsupported_intervals
                )
            )
        )

    allowed_providers = {
        "eodhd",
        "yfinance",
    }

    unsupported_providers = (
        set(providers)
        - allowed_providers
    )

    if unsupported_providers:
        raise ValueError(
            "unsupported acquisition provider(s): "
            + ", ".join(
                sorted(
                    unsupported_providers
                )
            )
        )

    workspace = (
        artifact_dir
        / "stocks_reference_market_data"
    )

    workspace.mkdir(
        parents=True,
        exist_ok=False,
    )

    inventory = provider_inventory(
        workspace
    )

    collection = collect_multitimeframe_data(
        workspace,
        symbols=symbols,
        intervals=intervals,
        providers=providers,
        start=payload.get(
            "start"
        ),
        end=payload.get(
            "end"
        ),
        lookback_days=int(
            payload.get(
                "lookback_days",
                60,
            )
        ),
    )

    validation = (
        validate_multitimeframe_cache(
            workspace
        )
    )

    status = multitimeframe_status(
        workspace
    )

    audit = audit_multitimeframe_sources(
        workspace
    )

    private_root = (
        workspace
        / "data"
        / "research"
        / "multitimeframe"
        / "private"
    )

    bars = []

    for path in sorted(
        private_root.rglob(
            "bars.parquet"
        )
    ):
        bars.append(
            {
                "path": str(
                    path
                ),
                "relative_path": str(
                    path.relative_to(
                        artifact_dir
                    )
                ),
                "provider": _partition_value(
                    path,
                    "provider=",
                ),
                "symbol": _partition_value(
                    path,
                    "symbol=",
                ),
                "interval": _partition_value(
                    path,
                    "interval=",
                ),
                "source_interval": (
                    _partition_value(
                        path,
                        "source_interval=",
                    )
                ),
                "size_bytes": (
                    path.stat().st_size
                ),
            }
        )

    index_path = (
        artifact_dir
        / "stocks_reference_market_data_index.json"
    )

    index_payload = {
        "schema": (
            "stocks_reference_market_data_index_v1"
        ),
        "symbols": symbols,
        "intervals": intervals,
        "providers": providers,
        "workspace": str(
            workspace
        ),
        "bar_file_count": len(
            bars
        ),
        "bars": bars,
        "inventory_status": (
            inventory.get(
                "status"
            )
        ),
        "collection_status": (
            collection.get(
                "status"
            )
        ),
        "validation_status": (
            validation.get(
                "status"
            )
        ),
        "current_data_status": (
            status.get(
                "current_data_status"
            )
        ),
        "coverage_ratio": (
            status.get(
                "coverage_ratio"
            )
        ),
        "material_divergence_count": (
            audit.get(
                "material_divergence_count"
            )
        ),
        "execution_authority": "NONE",
        "broker_calls": 0,
    }

    index_path.write_text(
        json.dumps(
            index_payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    artifacts = [
        artifact_ref(
            index_path,
            media_type="application/json",
            rows=len(
                bars
            ),
        )
    ]

    output_root = (
        workspace
        / "output"
        / "research"
        / "multitimeframe"
    )

    for name in (
        "provider-inventory.json",
        "collection-manifest.json",
        "cache-validation.json",
        "status.json",
        "cross-provider-audit.json",
        "privacy-audit.json",
    ):
        path = (
            output_root
            / name
        )

        if path.is_file():
            artifacts.append(
                artifact_ref(
                    path,
                    media_type=(
                        "application/json"
                    ),
                )
            )

    state = (
        "OK"
        if (
            collection.get(
                "status"
            )
            == "GO"
            and validation.get(
                "status"
            )
            == "GO"
        )
        else "DEGRADED"
    )

    warnings = []

    if (
        audit.get(
            "material_divergence_count",
            0,
        )
    ):
        warnings.append(
            "cross-provider material divergence detected"
        )

    return {
        "state": state,
        "data": {
            "symbols": symbols,
            "intervals": intervals,
            "providers": providers,
            "workspace": str(
                workspace
            ),
            "bar_file_count": len(
                bars
            ),
            "collection_status": (
                collection.get(
                    "status"
                )
            ),
            "validation_status": (
                validation.get(
                    "status"
                )
            ),
            "multi_timeframe_status": (
                status.get(
                    "status"
                )
            ),
            "current_data_status": (
                status.get(
                    "current_data_status"
                )
            ),
            "coverage_ratio": (
                status.get(
                    "coverage_ratio"
                )
            ),
            "current_data_ratio": (
                status.get(
                    "current_data_ratio"
                )
            ),
            "material_divergence_count": (
                audit.get(
                    "material_divergence_count",
                    0,
                )
            ),
            "execution_authority": (
                "NONE"
            ),
            "broker_calls": 0,
        },
        "artifacts": artifacts,
        "warnings": warnings,
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

    if action == "multitimeframe_collect":
        return _multitimeframe_collect(
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
