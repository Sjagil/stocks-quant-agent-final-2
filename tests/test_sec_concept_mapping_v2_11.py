from __future__ import annotations

from datetime import date

from stocks.research.sec_fundamentals import (
    build_sec_fundamentals_payload,
)


def _obs(value: float):
    return [
        {
            "val": value,
            "end": "2026-06-30",
            "filed": "2026-08-05",
            "form": "10-Q",
            "accn": "x",
        }
    ]


def test_convertible_debt_noncurrent_is_accepted_as_debt():
    facts = {
        "facts": {
            "us-gaap": {
                "ConvertibleDebtNoncurrent": {
                    "units": {"USD": _obs(0.0)}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": _obs(100.0)}
                },
                "AccountsReceivableNetCurrent": {
                    "units": {"USD": _obs(50.0)}
                },
            }
        }
    }

    payload, provenance = build_sec_fundamentals_payload(
        "TEST",
        decision_date=date(2026, 8, 14),
        market_cap=1000.0,
        submissions={"name": "Test", "sicDescription": "Software"},
        companyfacts=facts,
    )

    report = next(
        iter(
            payload["Financials"]["Balance_Sheet"]["quarterly"].values()
        )
    )
    assert report["longTermDebt"] == 0.0
    assert provenance["source"] == "SEC_COMPANYFACTS"


def test_ifrs_borrowings_and_trade_receivables_are_accepted():
    facts = {
        "facts": {
            "ifrs-full": {
                "Borrowings": {
                    "units": {"USD": _obs(120.0)}
                },
                "CashAndCashEquivalents": {
                    "units": {"USD": _obs(200.0)}
                },
                "TradeAndOtherCurrentReceivables": {
                    "units": {"USD": _obs(80.0)}
                },
            }
        }
    }

    payload, _ = build_sec_fundamentals_payload(
        "TEST",
        decision_date=date(2026, 8, 14),
        market_cap=1000.0,
        submissions={"name": "Test", "sicDescription": "Technology"},
        companyfacts=facts,
    )

    report = next(
        iter(
            payload["Financials"]["Balance_Sheet"]["quarterly"].values()
        )
    )
    assert report["longTermDebt"] == 120.0
    assert report["netReceivables"] == 80.0


def test_non_usd_facts_remain_fail_closed():
    facts = {
        "facts": {
            "ifrs-full": {
                "Borrowings": {
                    "units": {"EUR": _obs(120.0)}
                },
                "CashAndCashEquivalents": {
                    "units": {"EUR": _obs(200.0)}
                },
                "TradeAndOtherCurrentReceivables": {
                    "units": {"EUR": _obs(80.0)}
                },
            }
        }
    }

    try:
        build_sec_fundamentals_payload(
            "TEST",
            decision_date=date(2026, 8, 14),
            market_cap=1000.0,
            submissions={"name": "Test", "sicDescription": "Technology"},
            companyfacts=facts,
        )
    except ValueError as exc:
        assert "debt facts incomplete" in str(exc)
    else:
        raise AssertionError("non-USD facts must not be silently converted")
