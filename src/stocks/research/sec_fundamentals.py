from __future__ import annotations

import math
import os
import time
from datetime import date
from typing import Any, Iterable

import pandas as pd

from stocks.providers.http import ProviderHTTPClient


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_COMPANYFACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
)

DEFAULT_SEC_USER_AGENT = (
    "stocks-quant-agent-final-2 research "
    "https://github.com/Sjagil/stocks-quant-agent-final-2"
)

DEFAULT_FORMS = frozenset(
    {
        "10-Q",
        "10-Q/A",
        "10-K",
        "10-K/A",
        "20-F",
        "20-F/A",
        "40-F",
        "40-F/A",
    }
)


def sec_user_agent() -> str:
    configured = os.environ.get("SEC_USER_AGENT", "").strip()
    if not configured:
        raise ValueError("SEC_USER_AGENT_REQUIRED")
    if "@" not in configured:
        raise ValueError("SEC_USER_AGENT_CONTACT_EMAIL_REQUIRED")
    return configured


def _sec_get(
    client: ProviderHTTPClient,
    url: str,
    *,
    user_agent: str,
) -> Any:
    # Stay comfortably below the SEC's published fair-access ceiling.
    time.sleep(0.12)
    return client.get_json(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": url.split("/")[2],
        },
    )


def normalize_ticker_map(payload: Any) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError("SEC ticker map is not an object")

    result: dict[str, int] = {}

    for row in payload.values():
        if not isinstance(row, dict):
            continue

        ticker = str(row.get("ticker") or "").strip().upper()

        try:
            cik = int(row.get("cik_str"))
        except (TypeError, ValueError):
            continue

        if ticker and cik > 0:
            result[ticker] = cik

    if not result:
        raise ValueError("SEC ticker map contains no usable rows")

    return result


def fetch_ticker_map(
    client: ProviderHTTPClient,
    *,
    user_agent: str | None = None,
) -> dict[str, int]:
    payload = _sec_get(
        client,
        SEC_TICKERS_URL,
        user_agent=user_agent or sec_user_agent(),
    )
    return normalize_ticker_map(payload)


def fetch_company_documents(
    client: ProviderHTTPClient,
    *,
    cik: int,
    user_agent: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    agent = user_agent or sec_user_agent()

    submissions = _sec_get(
        client,
        SEC_SUBMISSIONS_URL.format(cik=int(cik)),
        user_agent=agent,
    )
    companyfacts = _sec_get(
        client,
        SEC_COMPANYFACTS_URL.format(cik=int(cik)),
        user_agent=agent,
    )

    if not isinstance(submissions, dict):
        raise ValueError("SEC submissions response is not an object")

    if not isinstance(companyfacts, dict):
        raise ValueError("SEC companyfacts response is not an object")

    return submissions, companyfacts


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def select_sec_fact(
    companyfacts: dict[str, Any],
    *,
    concepts: Iterable[str],
    decision_date: date,
    allowed_forms: set[str] | frozenset[str] = DEFAULT_FORMS,
) -> dict[str, Any] | None:
    facts_root = companyfacts.get("facts") or {}
    candidates: list[dict[str, Any]] = []

    for taxonomy in ("us-gaap", "ifrs-full"):
        taxonomy_facts = facts_root.get(taxonomy) or {}

        for concept in concepts:
            raw = taxonomy_facts.get(str(concept)) or {}
            units = raw.get("units") or {}

            for unit, observations in units.items():
                if unit != "USD":
                    continue
                if not isinstance(observations, list):
                    continue

                for observation in observations:
                    if not isinstance(observation, dict):
                        continue

                    form = str(observation.get("form") or "")
                    if form not in allowed_forms:
                        continue

                    raw_filed = observation.get("filed")
                    raw_end = observation.get("end")
                    if not raw_filed or not raw_end:
                        continue

                    try:
                        filed = pd.Timestamp(str(raw_filed)).date()
                        end = pd.Timestamp(str(raw_end)).date()
                    except Exception:
                        continue

                    # Strict PIT rule. Future filings and future report periods
                    # can never enter an earlier decision.
                    if filed > decision_date or end > decision_date:
                        continue

                    value = _finite(observation.get("val"))
                    if value is None or value < 0:
                        continue

                    candidates.append(
                        {
                            "taxonomy": taxonomy,
                            "concept": str(concept),
                            "unit": unit,
                            "value": value,
                            "end": end,
                            "filed": filed,
                            "form": form,
                            "accn": observation.get("accn"),
                        }
                    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda row: (
            row["end"],
            row["filed"],
            str(row.get("accn") or ""),
        )
    )
    return candidates[-1]


def _latest_value(
    companyfacts: dict[str, Any],
    concepts: Iterable[str],
    *,
    decision_date: date,
    allowed_forms: set[str] | frozenset[str],
) -> dict[str, Any] | None:
    return select_sec_fact(
        companyfacts,
        concepts=concepts,
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )


def _max_value(*facts: dict[str, Any] | None) -> float | None:
    values = [
        float(item["value"])
        for item in facts
        if item is not None
    ]
    return max(values) if values else None


def build_sec_fundamentals_payload(
    symbol: str,
    *,
    decision_date: date,
    market_cap: float | None,
    submissions: dict[str, Any],
    companyfacts: dict[str, Any],
    allowed_forms: set[str] | frozenset[str] = DEFAULT_FORMS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if market_cap is None or not math.isfinite(float(market_cap)):
        raise ValueError(f"{symbol}: current as-of market cap unavailable")

    total_debt = _latest_value(
        companyfacts,
        (
            "LongTermDebtAndFinanceLeaseObligations",
            "LongTermDebt",
            "DebtAndFinanceLeaseObligations",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )
    current_debt = _latest_value(
        companyfacts,
        (
            "LongTermDebtAndFinanceLeaseObligationsCurrent",
            "LongTermDebtCurrent",
            "ShortTermBorrowings",
            "ShortTermDebtCurrent",
            "CurrentBorrowings",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )
    noncurrent_debt = _latest_value(
        companyfacts,
        (
            "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
            "LongTermDebtNoncurrent",
            "NoncurrentBorrowings",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )
    short_borrowings = _latest_value(
        companyfacts,
        (
            "ShortTermBorrowings",
            "ShortTermDebtCurrent",
            "CurrentBorrowings",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )

    debt_candidates: list[float] = []
    if total_debt is not None:
        debt_candidates.append(float(total_debt["value"]))
    if current_debt is not None or noncurrent_debt is not None:
        debt_candidates.append(
            float((current_debt or {"value": 0.0})["value"])
            + float((noncurrent_debt or {"value": 0.0})["value"])
        )
    if short_borrowings is not None or noncurrent_debt is not None:
        debt_candidates.append(
            float((short_borrowings or {"value": 0.0})["value"])
            + float((noncurrent_debt or {"value": 0.0})["value"])
        )

    debt = max(debt_candidates) if debt_candidates else None

    cash = _latest_value(
        companyfacts,
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            "CashAndCashEquivalents",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )
    investments = _latest_value(
        companyfacts,
        (
            "ShortTermInvestments",
            "MarketableSecuritiesCurrent",
            "CurrentFinancialAssetsAtFairValueThroughProfitOrLoss",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )
    receivables = _latest_value(
        companyfacts,
        (
            "AccountsReceivableNetCurrent",
            "AccountsNotesAndLoansReceivableNetCurrent",
            "TradeAndOtherCurrentReceivables",
        ),
        decision_date=decision_date,
        allowed_forms=allowed_forms,
    )

    # Do not silently convert a missing accounting fact to zero.
    if debt is None:
        raise ValueError(f"{symbol}: SEC debt facts incomplete")
    if cash is None:
        raise ValueError(f"{symbol}: SEC cash facts incomplete")
    if receivables is None:
        raise ValueError(f"{symbol}: SEC receivables facts incomplete")

    cash_total = float(cash["value"])
    if investments is not None:
        cash_total += float(investments["value"])

    evidence = [
        item
        for item in (
            total_debt,
            current_debt,
            noncurrent_debt,
            short_borrowings,
            cash,
            investments,
            receivables,
        )
        if item is not None
    ]

    report_end = max(item["end"] for item in evidence)
    filing_date = max(item["filed"] for item in evidence)

    company_name = str(
        submissions.get("name")
        or companyfacts.get("entityName")
        or symbol
    )
    sic_description = str(
        submissions.get("sicDescription")
        or ""
    )

    payload = {
        "General": {
            "Name": company_name,
            "Sector": None,
            "Industry": sic_description,
        },
        "Highlights": {
            "MarketCapitalization": float(market_cap),
        },
        "Financials": {
            "Balance_Sheet": {
                "quarterly": {
                    report_end.isoformat(): {
                        "date": report_end.isoformat(),
                        "filing_date": filing_date.isoformat(),
                        "shortTermDebt": 0.0,
                        "longTermDebt": float(debt),
                        "cashAndShortTermInvestments": float(cash_total),
                        "netReceivables": float(receivables["value"]),
                    }
                }
            }
        },
    }

    provenance = {
        "source": "SEC_COMPANYFACTS",
        "entity_name": company_name,
        "sic": submissions.get("sic"),
        "sic_description": sic_description or None,
        "report_date": report_end.isoformat(),
        "filing_date": filing_date.isoformat(),
        "market_cap_source": "CONTEXTUAL_DISCOVERY_AS_OF",
        "concepts": sorted(
            {
                str(item["concept"])
                for item in evidence
            }
        ),
    }

    return payload, provenance


def fetch_sec_fundamentals(
    symbol: str,
    *,
    decision_date: date,
    market_cap: float | None,
    ticker_map: dict[str, int],
    client: ProviderHTTPClient,
    user_agent: str | None = None,
    allowed_forms: set[str] | frozenset[str] = DEFAULT_FORMS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ticker = str(symbol).strip().upper()
    cik = ticker_map.get(ticker)

    if cik is None:
        raise ValueError(f"{ticker}: SEC CIK mapping unavailable")

    submissions, companyfacts = fetch_company_documents(
        client,
        cik=cik,
        user_agent=user_agent,
    )

    payload, provenance = build_sec_fundamentals_payload(
        ticker,
        decision_date=decision_date,
        market_cap=market_cap,
        submissions=submissions,
        companyfacts=companyfacts,
        allowed_forms=allowed_forms,
    )
    provenance["cik"] = int(cik)
    return payload, provenance


__all__ = [
    "DEFAULT_FORMS",
    "build_sec_fundamentals_payload",
    "fetch_sec_fundamentals",
    "fetch_ticker_map",
    "normalize_ticker_map",
    "sec_user_agent",
    "select_sec_fact",
]
