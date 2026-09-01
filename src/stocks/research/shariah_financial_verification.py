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
from stocks.research.sec_fundamentals import (
    DEFAULT_FORMS,
    fetch_sec_fundamentals,
    fetch_ticker_map,
    sec_user_agent,
)
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

    market_cap = _number(highlights.get("MarketCapitalization"))
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
    )
    long_debt = _number(report.get("longTermDebt"))

    cash = _number(
        report.get("cashAndShortTermInvestments")
        or report.get("cashAndEquivalents")
        or report.get("cash")
    )

    receivables = _number(
        report.get("netReceivables")
        or report.get("receivables")
        or report.get("accountsReceivable")
    )

    # Never treat unavailable accounting data as zero.
    if short_debt is None and long_debt is None:
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
            report_date=str(report.get("date") or "") or None,
            filing_date=str(
                report.get("filing_date")
                or report.get("filingDate")
                or report.get("date")
                or ""
            ) or None,
            methodology=None,
            attestation_source=None,
            reason_codes=("MISSING_DEBT_FACTS",),
        )

    if cash is None or receivables is None:
        missing = []
        if cash is None:
            missing.append("MISSING_CASH_FACTS")
        if receivables is None:
            missing.append("MISSING_RECEIVABLES_FACTS")
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
            report_date=str(report.get("date") or "") or None,
            filing_date=str(
                report.get("filing_date")
                or report.get("filingDate")
                or report.get("date")
                or ""
            ) or None,
            methodology=None,
            attestation_source=None,
            reason_codes=tuple(missing),
        )

    debt_ratio = (
        float(short_debt or 0.0)
        + float(long_debt or 0.0)
    ) / market_cap
    cash_ratio = float(cash) / market_cap
    receivables_ratio = float(receivables) / market_cap

    ratio_failures: list[str] = []

    if debt_ratio > float(policy["debt_to_market_cap_max"]):
        ratio_failures.append("DEBT_RATIO")

    if cash_ratio > float(
        policy["cash_and_interest_securities_to_market_cap_max"]
    ):
        ratio_failures.append("CASH_RATIO")

    if receivables_ratio > float(
        policy["receivables_to_market_cap_max"]
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


def _policy(root: Path) -> dict[str, Any]:
    v28 = root / "config/final_decision_fabric_v2_8.json"
    if v28.is_file():
        return json.loads(v28.read_text(encoding="utf-8"))["shariah"]

    return json.loads(
        (
            root
            / "config/final_decision_fabric_v2_7.json"
        ).read_text(encoding="utf-8")
    )["shariah"]


def _incomplete_row(
    symbol: str,
    *,
    provider_errors: list[str],
) -> dict[str, Any]:
    return {
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
        "reason_codes": tuple(provider_errors),
        "fundamentals_source": None,
        "provider_error": " | ".join(provider_errors),
        "execution_authority": "NONE",
    }


def run_verification(
    project_root: str | Path,
    *,
    symbols: list[str],
    as_of: str,
    market_caps: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(project_root).resolve()
    policy = _policy(root)
    decision_date = pd.Timestamp(as_of).date()
    attestations = load_attestations(root)
    caps = {
        str(key).upper(): float(value)
        for key, value in (market_caps or {}).items()
        if _number(value) is not None
    }

    load_project_env(root)
    eodhd_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )

    allowed_forms = set(
        policy.get(
            "sec_allowed_forms",
            sorted(DEFAULT_FORMS),
        )
    )

    rows: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    ticker_map: dict[str, int] | None = None
    ticker_map_error: str | None = None

    with ProviderHTTPClient(
        user_agent=(
            "stocks-quant-agent/"
            "shariah-financial-verification-v2.8"
        )
    ) as client:
        for symbol in sorted(
            {
                str(item).strip().upper()
                for item in symbols
                if str(item).strip()
            }
        ):
            errors: list[str] = []
            row: dict[str, Any] | None = None

            if eodhd_key and bool(policy.get("eodhd_first", True)):
                try:
                    payload = fetch_fundamentals(
                        symbol,
                        api_key=eodhd_key,
                        client=client,
                    )
                    result = evaluate_financials(
                        symbol,
                        payload,
                        decision_date=decision_date,
                        policy=policy,
                        attestation=attestations.get(symbol),
                    )

                    # If EODHD actually supplied usable accounting data, keep it.
                    if result.status != "SHARIAH_DATA_INCOMPLETE":
                        row = result.to_dict()
                        row["fundamentals_source"] = "EODHD_FUNDAMENTALS"
                        row["provider_error"] = None
                    else:
                        errors.append(
                            "EODHD_INCOMPLETE:"
                            + ",".join(result.reason_codes)
                        )
                except Exception as exc:
                    errors.append(
                        f"EODHD:{type(exc).__name__}:{exc}"
                    )
            elif not eodhd_key:
                errors.append("EODHD:API_KEY_NOT_CONFIGURED")

            if row is None and bool(policy.get("sec_fallback", True)):
                try:
                    if ticker_map is None and ticker_map_error is None:
                        try:
                            ticker_map = fetch_ticker_map(
                                client,
                                user_agent=sec_user_agent(),
                            )
                        except Exception as exc:
                            ticker_map_error = (
                                f"{type(exc).__name__}:{exc}"
                            )

                    if ticker_map is None:
                        raise ValueError(
                            "SEC ticker map unavailable: "
                            + str(ticker_map_error)
                        )

                    sec_payload, provenance = fetch_sec_fundamentals(
                        symbol,
                        decision_date=decision_date,
                        market_cap=caps.get(symbol),
                        ticker_map=ticker_map,
                        client=client,
                        user_agent=sec_user_agent(),
                        allowed_forms=allowed_forms,
                    )
                    result = evaluate_financials(
                        symbol,
                        sec_payload,
                        decision_date=decision_date,
                        policy=policy,
                        attestation=attestations.get(symbol),
                    )
                    row = result.to_dict()
                    row["fundamentals_source"] = "SEC_COMPANYFACTS"
                    row["provider_error"] = (
                        " | ".join(errors)
                        if errors
                        else None
                    )
                    row["fundamentals_provenance"] = json.dumps(
                        provenance,
                        sort_keys=True,
                        default=str,
                    )
                except Exception as exc:
                    errors.append(
                        f"SEC:{type(exc).__name__}:{exc}"
                    )

            if row is None:
                row = _incomplete_row(
                    symbol,
                    provider_errors=errors,
                )

            source = str(row.get("fundamentals_source") or "NONE")
            source_counts[source] = source_counts.get(source, 0) + 1
            rows.append(row)

    frame = pd.DataFrame(rows)

    verified = (
        frame.get("trade_eligible", pd.Series(dtype=bool))
        .fillna(False)
        .astype(bool)
        if not frame.empty
        else pd.Series(dtype=bool)
    )

    audit = {
        "schema": "shariah_financial_verification_v2_8",
        "as_of": decision_date.isoformat(),
        "symbols": int(len(frame)),
        "verified_trade_eligible": int(verified.sum()),
        "financial_pass_pending_attestation": int(
            (
                frame.get("status", pd.Series(dtype=str))
                == "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
            ).sum()
        )
        if not frame.empty
        else 0,
        "ineligible": int(
            frame.get("status", pd.Series(dtype=str))
            .astype(str)
            .str.startswith("SHARIAH_INELIGIBLE")
            .sum()
        )
        if not frame.empty
        else 0,
        "data_incomplete": int(
            (
                frame.get("status", pd.Series(dtype=str))
                == "SHARIAH_DATA_INCOMPLETE"
            ).sum()
        )
        if not frame.empty
        else 0,
        "fundamentals_sources": source_counts,
        "financial_screen_grants_live_eligibility": False,
        "sec_fallback_enabled": bool(policy.get("sec_fallback", True)),
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }

    return frame, audit
