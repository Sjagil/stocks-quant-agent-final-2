
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.providers.eodhd import EODHD_BASE_URL
from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.research.shariah_research_precheck import business_precheck


@dataclass(frozen=True)
class ShariahVerification:
    symbol: str
    status: str
    business_status: str
    financial_ratio_status: str
    verified_attestation: bool
    trade_eligible: bool
    debt_to_market_cap: float | None
    cash_to_market_cap: float | None
    receivables_to_market_cap: float | None
    market_cap: float | None
    report_date: str | None
    filing_date: str | None
    methodology: str | None
    attestation_source: str | None
    reason_codes: tuple[str, ...]
    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _latest_report(
    reports: Any,
    *,
    decision_date: date,
) -> dict[str, Any] | None:
    if isinstance(reports, dict):
        values = list(reports.values())
    elif isinstance(reports, list):
        values = reports
    else:
        return None

    eligible: list[tuple[date, date, dict[str, Any]]] = []

    for row in values:
        if not isinstance(row, dict):
            continue

        raw_date = row.get("date")
        raw_filing = (
            row.get("filing_date")
            or row.get("filingDate")
            or raw_date
        )
        if not raw_date or not raw_filing:
            continue

        try:
            report_date = pd.Timestamp(str(raw_date)).date()
            filing_date = pd.Timestamp(str(raw_filing)).date()
        except Exception:
            continue

        # PIT rule: the report may only exist for a decision after filing.
        if filing_date <= decision_date:
            eligible.append((filing_date, report_date, row))

    if not eligible:
        return None

    eligible.sort(key=lambda item: (item[0], item[1]))
    return eligible[-1][2]


def _section(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def load_attestations(project_root: Path) -> dict[str, dict[str, Any]]:
    paths = (
        project_root / "config/shariah_verified_attestations_v1.json",
        project_root
        / "references/Stocks/config/screener/shariah_attestations_v1.json",
    )
    merged: dict[str, dict[str, Any]] = {}

    for path in paths:
        if not path.is_file():
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        candidates = raw.get("attestations", raw.get("symbols", raw))

        if isinstance(candidates, dict):
            iterable = [
                {
                    "symbol": symbol,
                    **(row if isinstance(row, dict) else {}),
                }
                for symbol, row in candidates.items()
            ]
        elif isinstance(candidates, list):
            iterable = candidates
        else:
            continue

        for row in iterable:
            if not isinstance(row, dict):
                continue
            symbol = str(
                row.get("symbol")
                or row.get("ticker")
                or row.get("code")
                or ""
            ).strip().upper()
            if symbol:
                merged[symbol] = row

    return merged


def attestation_valid(
    row: dict[str, Any] | None,
    *,
    decision_date: date,
    maximum_age_days: int,
) -> bool:
    if not row:
        return False

    status = str(
        row.get("status")
        or row.get("shariah_status")
        or ""
    ).upper()

    if status not in {
        "SHARIAH_COMPLIANT",
        "SHARIAH_ELIGIBLE",
        "SHARIAH_ELIGIBLE_PIT",
        "VERIFIED",
    }:
        return False

    raw_screened = (
        row.get("screened_at")
        or row.get("verified_at")
        or row.get("as_of")
    )
    raw_expires = (
        row.get("expires_at")
        or row.get("valid_until")
    )

    if raw_expires:
        try:
            if decision_date > pd.Timestamp(str(raw_expires)).date():
                return False
        except Exception:
            return False

    if raw_screened:
        try:
            screened = pd.Timestamp(str(raw_screened)).date()
        except Exception:
            return False

        if screened > decision_date:
            return False

        if (decision_date - screened).days > int(maximum_age_days):
            return False

    return True


def fetch_fundamentals(
    symbol: str,
    *,
    api_key: str,
    client: ProviderHTTPClient,
) -> dict[str, Any]:
    payload = client.get_json(
        f"{EODHD_BASE_URL}/v1.1/fundamentals/{symbol.upper()}.US",
        params={
            "api_token": api_key,
            "fmt": "json",
        },
    )

    if not isinstance(payload, dict):
        raise ValueError(f"{symbol}: invalid fundamentals payload")

    return payload


def evaluate_financials(
    symbol: str,
    payload: dict[str, Any],
    *,
    decision_date: date,
    policy: dict[str, Any],
    attestation: dict[str, Any] | None,
) -> ShariahVerification:
    general = payload.get("General") or {}
    highlights = payload.get("Highlights") or {}

    precheck = business_precheck(
        sector=general.get("Sector"),
        industry=general.get("Industry"),
        name=general.get("Name"),
    )

    if precheck["status"] == "HARD_EXCLUSION_CANDIDATE":
        return ShariahVerification(
            symbol=symbol,
            status="SHARIAH_INELIGIBLE_BUSINESS",
            business_status=precheck["status"],
            financial_ratio_status="NOT_EVALUATED",
            verified_attestation=False,
            trade_eligible=False,
            debt_to_market_cap=None,
            cash_to_market_cap=None,
            receivables_to_market_cap=None,
            market_cap=_number(
                highlights.get("MarketCapitalization")
            ),
            report_date=None,
            filing_date=None,
            methodology=None,
            attestation_source=None,
            reason_codes=tuple(
                f"BUSINESS:{value}"
                for value in precheck["hard_matches"]
            ),
        )

    market_cap = _number(
        highlights.get("MarketCapitalization")
    )
    if market_cap is None:
        market_cap_mln = _number(
            highlights.get("MarketCapitalizationMln")
        )
        if market_cap_mln is not None:
            market_cap = market_cap_mln * 1_000_000.0

    quarterly = _section(
        payload,
        "Financials",
        "Balance_Sheet",
        "quarterly",
    )
    yearly = _section(
        payload,
        "Financials",
        "Balance_Sheet",
        "yearly",
    )

    report = _latest_report(
        quarterly,
        decision_date=decision_date,
    )
    if report is None:
        report = _latest_report(
            yearly,
            decision_date=decision_date,
        )

    if market_cap is None or market_cap <= 0 or report is None:
        return ShariahVerification(
            symbol=symbol,
            status="SHARIAH_DATA_INCOMPLETE",
            business_status=precheck["status"],
            financial_ratio_status="DATA_INCOMPLETE",
            verified_attestation=False,
            trade_eligible=False,
            debt_to_market_cap=None,
            cash_to_market_cap=None,
            receivables_to_market_cap=None,
            market_cap=market_cap,
            report_date=None,
            filing_date=None,
            methodology=None,
            attestation_source=None,
            reason_codes=("MISSING_MARKET_CAP_OR_PIT_BALANCE_SHEET",),
        )

    short_debt = _number(
        report.get("shortTermDebt")
        or report.get("shortLongTermDebt")
    ) or 0.0
    long_debt = _number(
        report.get("longTermDebt")
    ) or 0.0

    cash = _number(
        report.get("cashAndShortTermInvestments")
        or report.get("cashAndEquivalents")
        or report.get("cash")
    ) or 0.0

    receivables = _number(
        report.get("netReceivables")
        or report.get("receivables")
        or report.get("accountsReceivable")
    )

    debt_ratio = (short_debt + long_debt) / market_cap
    cash_ratio = cash / market_cap
    receivables_ratio = (
        receivables / market_cap
        if receivables is not None
        else None
    )

    ratio_failures: list[str] = []

    if debt_ratio > float(policy["debt_to_market_cap_max"]):
        ratio_failures.append("DEBT_RATIO")

    if cash_ratio > float(
        policy["cash_and_interest_securities_to_market_cap_max"]
    ):
        ratio_failures.append("CASH_RATIO")

    if (
        receivables_ratio is not None
        and receivables_ratio
        > float(policy["receivables_to_market_cap_max"])
    ):
        ratio_failures.append("RECEIVABLES_RATIO")

    report_date = (
        str(report.get("date"))
        if report.get("date")
        else None
    )
    filing_date = (
        str(
            report.get("filing_date")
            or report.get("filingDate")
            or report.get("date")
        )
        if (
            report.get("filing_date")
            or report.get("filingDate")
            or report.get("date")
        )
        else None
    )

    if ratio_failures:
        return ShariahVerification(
            symbol=symbol,
            status="SHARIAH_INELIGIBLE_FINANCIAL_RATIOS",
            business_status=precheck["status"],
            financial_ratio_status="FAIL",
            verified_attestation=False,
            trade_eligible=False,
            debt_to_market_cap=debt_ratio,
            cash_to_market_cap=cash_ratio,
            receivables_to_market_cap=receivables_ratio,
            market_cap=market_cap,
            report_date=report_date,
            filing_date=filing_date,
            methodology=None,
            attestation_source=None,
            reason_codes=tuple(ratio_failures),
        )

    verified = attestation_valid(
        attestation,
        decision_date=decision_date,
        maximum_age_days=int(
            policy["maximum_attestation_age_days"]
        ),
    )

    methodology = (
        str(attestation.get("methodology"))
        if verified and attestation
        else None
    )
    source = (
        str(attestation.get("source"))
        if verified and attestation
        else None
    )

    # The project's ratio pre-screen is not itself a religious certification.
    # Live eligibility remains fail-closed behind an explicit attestation.
    status = (
        "SHARIAH_ELIGIBLE_VERIFIED"
        if verified
        else "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
    )

    return ShariahVerification(
        symbol=symbol,
        status=status,
        business_status=precheck["status"],
        financial_ratio_status="PASS",
        verified_attestation=verified,
        trade_eligible=verified,
        debt_to_market_cap=debt_ratio,
        cash_to_market_cap=cash_ratio,
        receivables_to_market_cap=receivables_ratio,
        market_cap=market_cap,
        report_date=report_date,
        filing_date=filing_date,
        methodology=methodology,
        attestation_source=source,
        reason_codes=(
            ()
            if verified
            else (
                "VERIFIED_ATTESTATION_REQUIRED",
                "NON_PERMISSIBLE_INCOME_REQUIRES_ATTESTATION",
            )
        ),
    )


def run_verification(
    project_root: str | Path,
    *,
    symbols: list[str],
    as_of: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()

    policy = json.loads(
        (
            root
            / "config/final_decision_fabric_v2_7.json"
        ).read_text(encoding="utf-8")
    )["shariah"]

    decision_date = pd.Timestamp(as_of).date()
    attestations = load_attestations(root)

    load_project_env(root)
    api_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )

    if not api_key:
        raise ValueError(
            "EODHD API key is required for financial verification"
        )

    rows = []

    with ProviderHTTPClient(
        user_agent=(
            "stocks-quant-agent/"
            "shariah-financial-verification-v2.7"
        )
    ) as client:
        for symbol in sorted(
            {
                str(item).strip().upper()
                for item in symbols
                if str(item).strip()
            }
        ):
            try:
                payload = fetch_fundamentals(
                    symbol,
                    api_key=api_key,
                    client=client,
                )
                result = evaluate_financials(
                    symbol,
                    payload,
                    decision_date=decision_date,
                    policy=policy,
                    attestation=attestations.get(symbol),
                )
                row = result.to_dict()
            except Exception as exc:
                row = {
                    "symbol": symbol,
                    "status": "SHARIAH_DATA_INCOMPLETE",
                    "business_status": "UNKNOWN",
                    "financial_ratio_status": "DATA_INCOMPLETE",
                    "verified_attestation": False,
                    "trade_eligible": False,
                    "debt_to_market_cap": None,
                    "cash_to_market_cap": None,
                    "receivables_to_market_cap": None,
                    "market_cap": None,
                    "report_date": None,
                    "filing_date": None,
                    "methodology": None,
                    "attestation_source": None,
                    "reason_codes": (
                        f"{type(exc).__name__}:{exc}",
                    ),
                    "execution_authority": "NONE",
                }
            rows.append(row)

    frame = pd.DataFrame(rows)

    audit = {
        "schema": "shariah_financial_verification_v2_7",
        "symbols": int(len(frame)),
        "verified_trade_eligible": int(
            frame.get(
                "trade_eligible",
                pd.Series(dtype=bool),
            )
            .fillna(False)
            .astype(bool)
            .sum()
        )
        if not frame.empty
        else 0,
        "financial_pass_pending_attestation": int(
            (
                frame.get(
                    "status",
                    pd.Series(dtype=str),
                )
                == "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
            ).sum()
        )
        if not frame.empty
        else 0,
        "ineligible": int(
            frame.get(
                "status",
                pd.Series(dtype=str),
            )
            .astype(str)
            .str.startswith("SHARIAH_INELIGIBLE")
            .sum()
        )
        if not frame.empty
        else 0,
        "data_incomplete": int(
            (
                frame.get(
                    "status",
                    pd.Series(dtype=str),
                )
                == "SHARIAH_DATA_INCOMPLETE"
            ).sum()
        )
        if not frame.empty
        else 0,
        "financial_screen_grants_live_eligibility": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }

    return frame, audit
