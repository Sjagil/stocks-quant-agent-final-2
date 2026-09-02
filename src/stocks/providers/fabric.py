from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from stocks.capabilities import (
    CapabilityRegistry,
)
from stocks.providers.adapters import (
    alphavantage_news,
    currents_news,
    eodhd_news,
    finnhub_news,
    finnhub_quote,
    fmp_bundle,
    fmp_news,
    marketaux_news,
    marketstack_bars,
    openfigi_mapping,
    polygon_snapshot,
    rss_news,
    thetadata_expirations,
    twelvedata_bars,
    yahoo_fundamentals,
    yahoo_news,
    yahoo_options,
    yahoo_snapshot,
)
from stocks.providers.contracts import (
    SourceResult,
    SourceState,
)
from stocks.providers.federation_v2_27 import (
    assert_payload_contains_no_secrets,
    sanitize_payload,
)
from stocks.providers.openexchange import latest_fx


class SourceFabric:
    def __init__(
        self,
        project_root: str | Path,
    ) -> None:
        self.project_root = (
            Path(project_root)
            .resolve()
        )

    @staticmethod
    def _safe(
        provider: str,
        domain: str,
        function: Callable[[], SourceResult],
    ) -> SourceResult:
        try:
            return function()

        except Exception as exc:
            return SourceResult(
                provider=provider,
                domain=domain,
                state=SourceState.ERROR,
                error=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            ).finish()

    def refresh_symbol(
        self,
        symbol: str,
        *,
        market: bool = True,
        news: bool = True,
        fundamentals: bool = True,
        options: bool = True,
        mapping: bool = True,
    ) -> dict:
        symbol = (
            symbol.strip().upper()
        )

        results: list[
            SourceResult
        ] = []

        if market:
            results.extend(
                [
                    self._safe(
                        "polygon",
                        "live_quotes",
                        lambda:
                        polygon_snapshot(
                            symbol
                        ),
                    ),
                    self._safe(
                        "twelvedata",
                        "bars",
                        lambda:
                        twelvedata_bars(
                            symbol
                        ),
                    ),
                    self._safe(
                        "finnhub",
                        "live_quotes",
                        lambda:
                        finnhub_quote(
                            symbol
                        ),
                    ),
                    self._safe(
                        "marketstack",
                        "bars",
                        lambda:
                        marketstack_bars(
                            symbol
                        ),
                    ),
                    self._safe(
                        "yfinance",
                        "bars",
                        lambda:
                        yahoo_snapshot(
                            symbol
                        ),
                    ),
                ]
            )

        if news:
            results.extend(
                [
                    self._safe(
                        "eodhd",
                        "news",
                        lambda:
                        eodhd_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "alphavantage",
                        "news",
                        lambda:
                        alphavantage_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "marketaux",
                        "news",
                        lambda:
                        marketaux_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "currents",
                        "news",
                        lambda:
                        currents_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "finnhub",
                        "news",
                        lambda:
                        finnhub_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "fmp",
                        "news",
                        lambda:
                        fmp_news(
                            symbol
                        ),
                    ),
                    self._safe(
                        "yfinance",
                        "news",
                        lambda:
                        yahoo_news(
                            symbol
                        ),
                    ),
                ]
            )

        if fundamentals:
            results.extend(
                [
                    self._safe(
                        "fmp",
                        "fundamentals",
                        lambda:
                        fmp_bundle(
                            symbol
                        ),
                    ),
                    self._safe(
                        "yfinance",
                        "fundamentals",
                        lambda:
                        yahoo_fundamentals(
                            symbol
                        ),
                    ),
                ]
            )

        if options:
            results.extend(
                [
                    self._safe(
                        "thetadata",
                        "options",
                        lambda:
                        thetadata_expirations(
                            symbol
                        ),
                    ),
                    self._safe(
                        "yfinance",
                        "options",
                        lambda:
                        yahoo_options(
                            symbol
                        ),
                    ),
                ]
            )

        if mapping:
            results.append(
                self._safe(
                    "openfigi",
                    "symbol_mapping",
                    lambda:
                    openfigi_mapping(
                        symbol
                    ),
                )
            )

        return {
            "symbol": symbol,
            "results": [
                result.to_dict()
                for result in results
            ],
        }

    def global_sources(
        self,
    ) -> dict:
        rss = self._safe(
            "rss",
            "news",
            lambda:
            rss_news(
                self.project_root
            ),
        )
        fx = self._safe(
            "openexchangerates",
            "fx",
            lambda: latest_fx(),
        )

        return {
            "results": [
                rss.to_dict(),
                fx.to_dict(),
            ]
        }

    def engine_health(
        self,
    ) -> dict:
        registry = (
            CapabilityRegistry.load(
                self.project_root
                / "config"
                / "capabilities.yaml",
                project_root=(
                    self.project_root
                ),
            )
        )

        health = (
            registry.health_all()
        )

        return {
            name: value.as_dict()
            for name, value
            in health.items()
        }

    def run(
        self,
        symbols: tuple[str, ...],
        *,
        include_engines: bool = False,
    ) -> dict:
        created = datetime.now(
            timezone.utc
        )

        payload = {
            "schema": (
                "source_fabric_refresh_v3"
            ),
            "created_at": (
                created.isoformat()
            ),
            "execution_authority": (
                "NONE"
            ),
            "broker_order_calls": 0,
            "symbols": {},
            "global": (
                self.global_sources()
            ),
        }

        for symbol in symbols:
            payload[
                "symbols"
            ][symbol.upper()] = (
                self.refresh_symbol(
                    symbol
                )
            )

        if include_engines:
            payload[
                "research_engines"
            ] = self.engine_health()

        output_dir = (
            self.project_root
            / "artifacts"
            / "source_fabric"
            / "refresh"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifact = (
            output_dir
            / (
                "refresh-"
                + created.strftime(
                    "%Y%m%dT%H%M%SZ"
                )
                + ".json"
            )
        )

        safe_payload, secret_audit = sanitize_payload(
            payload
        )
        safe_payload[
            "secret_redaction_audit"
        ] = secret_audit
        assert_payload_contains_no_secrets(
            safe_payload
        )

        artifact.write_text(
            json.dumps(
                safe_payload,
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        safe_payload[
            "artifact"
        ] = str(
            artifact
        )

        return safe_payload
