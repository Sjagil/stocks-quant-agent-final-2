from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Iterable


class SourceDomain(StrEnum):
    BARS = "bars"
    LIVE_QUOTES = "live_quotes"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    EVENTS = "events"
    MACRO = "macro"
    FX = "fx"
    OPTIONS = "options"
    GEX = "gex"
    SYMBOL_MAPPING = "symbol_mapping"
    SCREENER = "screener"
    SENTIMENT = "sentiment"
    CROSS_ASSET = "cross_asset"


@dataclass(frozen=True)
class SourceSpec:
    name: str
    domains: tuple[SourceDomain, ...]
    env_any: tuple[str, ...] = ()
    env_all: tuple[str, ...] = ()
    requires_key: bool = True
    research: bool = True
    live_context: bool = False
    authoritative: bool = False
    notes: str = ""

    def configured(self) -> bool:
        if self.env_all:
            if not all(
                bool(os.environ.get(key, "").strip())
                for key in self.env_all
            ):
                return False

        if self.env_any:
            return any(
                bool(os.environ.get(key, "").strip())
                for key in self.env_any
            )

        return not self.requires_key

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["domains"] = [
            str(domain)
            for domain in self.domains
        ]
        payload["configured"] = self.configured()
        return payload


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        "ibkr",
        (
            SourceDomain.BARS,
            SourceDomain.LIVE_QUOTES,
            SourceDomain.OPTIONS,
        ),
        env_all=("IBKR_HOST", "IBKR_PORT"),
        requires_key=False,
        live_context=True,
        authoritative=True,
        notes="Live broker market state and executable quote context.",
    ),
    SourceSpec(
        "eodhd",
        (
            SourceDomain.BARS,
            SourceDomain.FUNDAMENTALS,
            SourceDomain.NEWS,
            SourceDomain.SYMBOL_MAPPING,
        ),
        env_any=("EODHD_API_KEY",),
        notes="Primary broad historical/research provider.",
    ),
    SourceSpec(
        "yfinance",
        (
            SourceDomain.BARS,
            SourceDomain.FUNDAMENTALS,
            SourceDomain.NEWS,
            SourceDomain.OPTIONS,
        ),
        requires_key=False,
        notes="Research fallback and independent cross-check.",
    ),
    SourceSpec(
        "polygon",
        (
            SourceDomain.BARS,
            SourceDomain.LIVE_QUOTES,
            SourceDomain.OPTIONS,
            SourceDomain.NEWS,
        ),
        env_any=("POLYGON_API_KEY",),
    ),
    SourceSpec(
        "twelvedata",
        (
            SourceDomain.BARS,
            SourceDomain.LIVE_QUOTES,
        ),
        env_any=("TWELVEDATA_API_KEY",),
    ),
    SourceSpec(
        "marketstack",
        (
            SourceDomain.BARS,
        ),
        env_any=("MARKETSTACK_API_KEY",),
    ),
    SourceSpec(
        "finnhub",
        (
            SourceDomain.BARS,
            SourceDomain.FUNDAMENTALS,
            SourceDomain.NEWS,
            SourceDomain.SENTIMENT,
        ),
        env_any=("FINNHUB_API_KEY",),
    ),
    SourceSpec(
        "fmp",
        (
            SourceDomain.FUNDAMENTALS,
            SourceDomain.NEWS,
        ),
        env_any=("FMP_API_KEY",),
    ),
    SourceSpec(
        "sec_edgar",
        (
            SourceDomain.FUNDAMENTALS,
            SourceDomain.EVENTS,
        ),
        requires_key=False,
        authoritative=True,
        notes="Official filing/event evidence.",
    ),
    SourceSpec(
        "fred",
        (
            SourceDomain.MACRO,
        ),
        env_any=("FRED_API_KEY",),
        authoritative=True,
    ),
    SourceSpec(
        "us_treasury_fiscaldata",
        (
            SourceDomain.MACRO,
        ),
        env_any=("FISCAL_API_KEY",),
        requires_key=False,
    ),
    SourceSpec(
        "nasdaq_data_link",
        (
            SourceDomain.MACRO,
            SourceDomain.CROSS_ASSET,
        ),
        env_any=("Nasdaq_API_KEY", "NASDAQ_API_KEY"),
    ),
    SourceSpec(
        "openexchangerates",
        (
            SourceDomain.FX,
        ),
        env_any=(
            "OPENEXCHANGERATES_APP_ID",
            "OPENEXCHANGE_API_KEY",
        ),
    ),
    SourceSpec(
        "currencylayer",
        (
            SourceDomain.FX,
        ),
        env_any=(
            "CURRENCYLAYER_API_KEY",
            "CURRENCYLAYER_ACCESS_KEY",
        ),
    ),
    SourceSpec(
        "alphavantage",
        (
            SourceDomain.NEWS,
            SourceDomain.SENTIMENT,
            SourceDomain.BARS,
        ),
        env_any=("ALPHAVANTAGE_API_KEY",),
    ),
    SourceSpec(
        "marketaux",
        (
            SourceDomain.NEWS,
            SourceDomain.SENTIMENT,
        ),
        env_any=("MARKETAUX_API_TOKEN",),
    ),
    SourceSpec(
        "currents",
        (
            SourceDomain.NEWS,
        ),
        env_any=("CURRENT_NEWS_API_KEY",),
    ),
    SourceSpec(
        "rss",
        (
            SourceDomain.NEWS,
            SourceDomain.EVENTS,
        ),
        requires_key=False,
    ),
    SourceSpec(
        "thetadata",
        (
            SourceDomain.OPTIONS,
            SourceDomain.GEX,
        ),
        env_any=("THETA_DATA_API_KEY",),
    ),
    SourceSpec(
        "openfigi",
        (
            SourceDomain.SYMBOL_MAPPING,
        ),
        env_any=("OPENFIGI_API_KEY",),
    ),
    SourceSpec(
        "dune",
        (
            SourceDomain.CROSS_ASSET,
        ),
        env_any=("DUNE_API_KEY",),
        notes="Optional cross-asset/on-chain contextual evidence.",
    ),
    SourceSpec(
        "stocks_reference_screener",
        (
            SourceDomain.SCREENER,
        ),
        requires_key=False,
        notes="Donor capability from references/Stocks.",
    ),
    SourceSpec(
        "stocks_reference_news",
        (
            SourceDomain.NEWS,
            SourceDomain.EVENTS,
        ),
        requires_key=False,
        notes="Donor capability from references/Stocks.",
    ),
    SourceSpec(
        "stocks_reference_sec",
        (
            SourceDomain.FUNDAMENTALS,
            SourceDomain.EVENTS,
        ),
        requires_key=False,
        notes="SEC donor capability from references/Stocks.",
    ),
)


def sources_for(
    domain: SourceDomain,
) -> tuple[SourceSpec, ...]:
    return tuple(
        source
        for source in SOURCES
        if domain in source.domains
    )


def configured_sources(
    domain: SourceDomain | None = None,
) -> tuple[SourceSpec, ...]:
    values: Iterable[SourceSpec] = (
        SOURCES
        if domain is None
        else sources_for(domain)
    )

    return tuple(
        source
        for source in values
        if source.configured()
    )
