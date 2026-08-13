from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceQuality:
    source: str
    completeness: float
    freshness: float
    consistency: float
    provenance: float
    authority: float

    @property
    def score(self) -> float:
        values = (
            self.completeness,
            self.freshness,
            self.consistency,
            self.provenance,
            self.authority,
        )

        return (
            sum(
                values
            )
            /
            len(
                values
            )
        )


DEFAULT_SOURCE_AUTHORITY = {
    "ibkr": 1.00,
    "sec_edgar": 1.00,
    "fred": 1.00,
    "us_treasury_fiscaldata": 1.00,

    "eodhd": 0.90,
    "polygon": 0.90,
    "fmp": 0.90,
    "thetadata": 0.90,

    "finnhub": 0.85,
    "twelvedata": 0.85,
    "alphavantage": 0.85,

    "marketstack": 0.75,
    "openexchangerates": 0.85,
    "currencylayer": 0.75,

    "marketaux": 0.75,
    "currents": 0.65,

    "yfinance": 0.70,
    "rss": 0.75,

    "stocks_reference_news": 0.90,
    "stocks_reference_sec": 0.95,
    "stocks_reference_screener": 0.90,
}


def authority_score(
    source: str,
) -> float:
    return float(
        DEFAULT_SOURCE_AUTHORITY.get(
            source,
            0.50,
        )
    )
