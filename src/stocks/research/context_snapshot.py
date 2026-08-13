from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from stocks.intelligence_agent.config import (
    AgentConfig,
)

from stocks.intelligence_agent.providers.eodhd import (
    EODHDProvider,
)

from stocks.intelligence_agent.providers.fred import (
    FredProvider,
)


MACRO_SERIES = (
    "VIXCLS",
    "DGS10",
    "DGS2",
    "T10Y2Y",
    "DFF",
)


def _series_summary(
    series: pd.Series,
) -> dict:
    clean = (
        pd.Series(
            series,
            copy=True,
        )
        .dropna()
        .sort_index()
    )

    if clean.empty:
        return {
            "status": "EMPTY",
        }

    def lag_change(
        lag: int,
    ) -> float | None:
        if len(clean) <= lag:
            return None

        return float(
            clean.iloc[-1]
            -
            clean.iloc[-1 - lag]
        )

    return {
        "status": "OK",
        "asof": str(
            clean.index[-1]
        ),
        "value": float(
            clean.iloc[-1]
        ),
        "change_1": (
            lag_change(1)
        ),
        "change_5": (
            lag_change(5)
        ),
        "change_20": (
            lag_change(20)
        ),
        "observations": len(
            clean
        ),
    }


def collect_macro(
    config: AgentConfig,
) -> dict:
    if not config.fred_api_key:
        return {
            "status": "MISSING_FRED_KEY",
        }

    provider = FredProvider(
        config.fred_api_key
    )

    start = (
        datetime.now(
            timezone.utc
        )
        -
        timedelta(
            days=550
        )
    ).date().isoformat()

    output = {}

    try:
        for series_id in MACRO_SERIES:
            try:
                series = provider.series(
                    series_id,
                    observation_start=start,
                )

                output[
                    series_id
                ] = _series_summary(
                    series
                )

            except Exception as exc:
                output[
                    series_id
                ] = {
                    "status": "ERROR",
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }

    finally:
        provider.close()

    return {
        "status": "OK",
        "series": output,
    }


def collect_news(
    config: AgentConfig,
    symbols: Iterable[str],
    *,
    lookback_days: int = 7,
    limit: int = 50,
) -> dict:
    if not config.eodhd_api_key:
        return {
            "status": "MISSING_EODHD_KEY",
        }

    provider = EODHDProvider(
        config.eodhd_api_key
    )

    today = datetime.now(
        timezone.utc
    ).date()

    start = (
        today
        -
        timedelta(
            days=lookback_days
        )
    ).isoformat()

    end = today.isoformat()

    output = {}

    try:
        for raw_symbol in symbols:
            symbol = raw_symbol.upper()

            provider_symbol = (
                symbol
                if "." in symbol
                else f"{symbol}.US"
            )

            try:
                articles = (
                    provider.fetch_news(
                        symbol=provider_symbol,
                        from_date=start,
                        to_date=end,
                        limit=limit,
                    )
                )

                provider_sentiment = (
                    provider.fetch_sentiment(
                        [provider_symbol],
                        from_date=start,
                        to_date=end,
                    )
                )

                articles = sorted(
                    articles,
                    key=lambda article:
                    article.published_at,
                    reverse=True,
                )

                output[
                    symbol
                ] = {
                    "status": "OK",
                    "article_count": len(
                        articles
                    ),
                    "provider_sentiment": (
                        provider_sentiment
                    ),
                    "latest_articles": [
                        {
                            "article_id": (
                                article.article_id
                            ),
                            "published_at": (
                                article.published_at.isoformat()
                            ),
                            "source": (
                                article.source
                            ),
                            "title": (
                                article.title
                            ),
                            "symbols": list(
                                article.symbols
                            ),
                            "tags": list(
                                article.tags
                            ),
                        }
                        for article in articles[
                            :15
                        ]
                    ],
                }

            except Exception as exc:
                output[
                    symbol
                ] = {
                    "status": "ERROR",
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }

    finally:
        provider.close()

    return {
        "status": "OK",
        "from": start,
        "to": end,
        "symbols": output,
    }


def collect_gex(
    symbols: Iterable[str],
) -> dict:
    from stocks.intelligence_agent.strategy1 import (
        StrategyConfig,
        calculate_gex,
    )

    output = {}

    for raw_symbol in symbols:
        symbol = raw_symbol.upper()

        try:
            result = calculate_gex(
                symbol,
                StrategyConfig(
                    symbol=symbol
                ),
            )

            output[
                symbol
            ] = {
                "status": "OK",
                **asdict(
                    result
                ),
            }

        except Exception as exc:
            output[
                symbol
            ] = {
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }

    return {
        "status": "OK",
        "symbols": output,
        "dealer_inventory_observed": False,
        "method": (
            "strategy1_gamma_exposure_proxy"
        ),
    }


def collect_context_snapshot(
    project_root: str | Path,
    symbols: Iterable[str],
    *,
    news: bool = True,
    macro: bool = True,
    gex: bool = True,
) -> dict:
    root = Path(
        project_root
    ).resolve()

    normalized_symbols = tuple(
        dict.fromkeys(
            symbol.strip().upper()
            for symbol in symbols
            if symbol.strip()
        )
    )

    config = AgentConfig()

    payload = {
        "schema": (
            "market_context_snapshot_v1"
        ),
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "symbols": list(
            normalized_symbols
        ),
        "execution_authority": "NONE",
        "broker_calls": 0,
    }

    if news:
        try:
            payload[
                "news"
            ] = collect_news(
                config,
                normalized_symbols,
            )
        except Exception as exc:
            payload[
                "news"
            ] = {
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }

    if macro:
        try:
            payload[
                "macro"
            ] = collect_macro(
                config
            )
        except Exception as exc:
            payload[
                "macro"
            ] = {
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }

    if gex:
        try:
            payload[
                "gex"
            ] = collect_gex(
                normalized_symbols
            )
        except Exception as exc:
            payload[
                "gex"
            ] = {
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }

    output_root = (
        root
        / "artifacts"
        / "context"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    artifact = (
        output_root
        / f"context-{timestamp}.json"
    )

    artifact.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    payload[
        "artifact"
    ] = str(
        artifact
    )

    return payload
