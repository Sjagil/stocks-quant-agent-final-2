from __future__ import annotations

from datetime import date

from stocks.providers.contracts import (
    SourceProvenance,
    SourceResult,
    SourceState,
)
from stocks.providers.env import secret
from stocks.providers.http import (
    ProviderHTTPClient,
)


BASE = (
    "https://openexchangerates.org/api"
)


def _app_id() -> str:
    return secret(
        "OPENEXCHANGERATES_APP_ID",
        "OPENEXCHANGE_API_KEY",
    )


def latest_fx(
    *,
    base: str = "EUR",
    symbols: tuple[str, ...] = (
        "USD",
        "GBP",
        "JPY",
        "CHF",
        "CAD",
        "AUD",
        "NZD",
        "CNY",
        "HKD",
        "KRW",
        "SGD",
    ),
) -> SourceResult:
    app_id = _app_id()

    if not app_id:
        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=SourceState.UNCONFIGURED,
        ).finish()

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                f"{BASE}/latest.json",
                params={
                    "app_id": app_id,
                    "base": base.upper(),
                    "symbols": ",".join(
                        symbols
                    ),
                },
            )

        rates = payload.get(
            "rates",
            {},
        )

        item = {
            "timestamp": payload.get(
                "timestamp"
            ),
            "base": payload.get(
                "base",
                base.upper(),
            ),
            "rates": rates,
        }

        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=(
                SourceState.OK
                if rates
                else SourceState.EMPTY
            ),
            items=[item],
            provenance=[
                SourceProvenance(
                    provider=(
                        "openexchangerates"
                    ),
                    domain="fx",
                    endpoint="/latest.json",
                    metadata={
                        "base": base.upper(),
                    },
                )
            ],
        ).finish()

    except Exception as exc:
        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=SourceState.ERROR,
            error=(
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        ).finish()


def historical_fx(
    day: date,
    *,
    base: str = "EUR",
    symbols: tuple[str, ...] = (
        "USD",
        "GBP",
        "JPY",
        "CHF",
        "CAD",
        "AUD",
        "CNY",
        "HKD",
        "KRW",
    ),
) -> SourceResult:
    app_id = _app_id()

    if not app_id:
        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=SourceState.UNCONFIGURED,
        ).finish()

    try:
        with ProviderHTTPClient() as client:
            payload = client.get_json(
                (
                    f"{BASE}/historical/"
                    f"{day.isoformat()}.json"
                ),
                params={
                    "app_id": app_id,
                    "base": base.upper(),
                    "symbols": ",".join(
                        symbols
                    ),
                },
            )

        rates = payload.get(
            "rates",
            {},
        )

        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=(
                SourceState.OK
                if rates
                else SourceState.EMPTY
            ),
            items=[
                {
                    "date": (
                        day.isoformat()
                    ),
                    "timestamp": (
                        payload.get(
                            "timestamp"
                        )
                    ),
                    "base": payload.get(
                        "base",
                        base.upper(),
                    ),
                    "rates": rates,
                }
            ],
        ).finish()

    except Exception as exc:
        return SourceResult(
            provider="openexchangerates",
            domain="fx",
            state=SourceState.ERROR,
            error=(
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        ).finish()
