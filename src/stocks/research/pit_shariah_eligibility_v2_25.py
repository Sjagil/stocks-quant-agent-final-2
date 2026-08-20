from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

SCHEMA = "pit_shariah_eligibility_v2_25"
AUTHORITY_NONE = "NONE"
PASS_ATTESTATION_STATUS = "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
VERIFIED_STATUS = "SHARIAH_ELIGIBLE_VERIFIED"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research_runtime/pit_shariah_eligibility_v2_25")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if value is pd.NaT:
        return None
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_safe(value),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _utc_series(values: pd.Series, *, field: str) -> pd.Series:
    result = pd.to_datetime(values, utc=True, errors="coerce")
    if result.isna().any():
        raise ValueError(f"{field} contains invalid timestamps")
    return result


def _date_available_at(value: Any, *, lag_days: int) -> pd.Timestamp | None:
    if value in (None, "") or pd.isna(value):
        return None
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    else:
        parsed = parsed.tz_convert("UTC")
    # Provider filing/screening dates are commonly date-only. Treat information
    # as available from the following UTC day unless an exact intraday timestamp
    # is supplied. This is conservative and prevents same-day look-ahead.
    text = str(value)
    has_clock = "T" in text or ":" in text
    if has_clock:
        return parsed
    return parsed.normalize() + pd.Timedelta(days=int(lag_days))


def _reason_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    text = str(value).strip()
    if text.startswith("(") or text.startswith("["):
        try:
            decoded = json.loads(text.replace("'", '"'))
            if isinstance(decoded, list):
                return "|".join(str(item) for item in decoded)
        except Exception:
            pass
    return text


@dataclass(frozen=True)
class PITHistoricalEligibilityPolicyV225:
    debt_to_market_cap_max: float = 0.30
    cash_to_market_cap_max: float = 0.30
    receivables_to_market_cap_max: float = 0.49
    maximum_attestation_age_days: int = 120
    date_only_availability_lag_days: int = 1
    require_business_state: bool = True
    require_market_cap: bool = True
    require_verified_attestation: bool = True

    def __post_init__(self) -> None:
        ratios = (
            self.debt_to_market_cap_max,
            self.cash_to_market_cap_max,
            self.receivables_to_market_cap_max,
        )
        if any(not 0 < float(value) < 1 for value in ratios):
            raise ValueError("Shariah ratio limits must be inside (0, 1)")
        if self.maximum_attestation_age_days < 1:
            raise ValueError("maximum_attestation_age_days must be positive")
        if self.date_only_availability_lag_days < 0:
            raise ValueError("date-only availability lag cannot be negative")


@dataclass(frozen=True)
class PITHistoricalEligibilityBundleV225:
    ledger: pd.DataFrame
    audit: Mapping[str, Any]


def current_verification_to_pit_events_v225(
    verification: pd.DataFrame,
    *,
    decision_time: str | pd.Timestamp,
    date_only_availability_lag_days: int = 1,
) -> pd.DataFrame:
    """Normalize the current verifier output into an auditable PIT event table.

    This does not make a current verification historically valid. It records
    exactly when the evidence in the current result became knowable so it can be
    used by backward as-of joins only from that point onward.
    """
    if verification.empty:
        return pd.DataFrame()
    required = {"symbol", "status", "trade_eligible", "filing_date"}
    missing = sorted(required.difference(verification.columns))
    if missing:
        raise ValueError(f"verification missing columns {missing}")
    cutoff = pd.Timestamp(decision_time)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    rows: list[dict[str, Any]] = []
    for raw in verification.to_dict(orient="records"):
        filing_available = _date_available_at(
            raw.get("filing_date"), lag_days=date_only_availability_lag_days
        )
        screened = raw.get("screened_at") or raw.get("verified_at") or raw.get("as_of")
        attestation_available = _date_available_at(
            screened, lag_days=date_only_availability_lag_days
        )
        evidence_times = [value for value in (filing_available, attestation_available) if value is not None]
        available_at = max(evidence_times) if evidence_times else cutoff
        rows.append(
            {
                **raw,
                "symbol": str(raw.get("symbol") or "").strip().upper(),
                "decision_time": cutoff,
                "available_at": available_at,
                "financial_available_at": filing_available,
                "attestation_available_at": attestation_available,
                "reason_codes": _reason_text(raw.get("reason_codes")),
                "pit_eligible_from": available_at,
                "historical_backfill_allowed": False,
                "execution_authority": AUTHORITY_NONE,
                "broker_calls": 0,
                "order_calls": 0,
            }
        )
    frame = pd.DataFrame(rows).sort_values(["symbol", "available_at"]).reset_index(drop=True)
    return frame


def build_attestation_queue_v225(verification: pd.DataFrame) -> pd.DataFrame:
    if verification.empty or "status" not in verification:
        return pd.DataFrame()
    queue = verification.loc[
        verification["status"].astype(str).eq(PASS_ATTESTATION_STATUS)
    ].copy()
    preferred = [
        "symbol",
        "debt_to_market_cap",
        "cash_to_market_cap",
        "receivables_to_market_cap",
        "market_cap",
        "report_date",
        "filing_date",
        "fundamentals_source",
        "business_status",
        "provider_error",
    ]
    columns = [column for column in preferred if column in queue.columns]
    queue = queue[columns].drop_duplicates(subset=["symbol"]).sort_values("symbol")
    if not queue.empty:
        queue["review_required"] = True
        queue["automatic_attestation"] = False
        queue["execution_authority"] = AUTHORITY_NONE
    return queue.reset_index(drop=True)


def _prepare_events(
    frame: pd.DataFrame,
    *,
    available_at: str,
    symbol: str = "symbol",
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    if symbol not in frame or available_at not in frame:
        raise ValueError(f"event table requires {symbol} and {available_at}")
    result = frame.copy()
    result[symbol] = result[symbol].astype(str).str.upper().str.strip()
    result[available_at] = _utc_series(result[available_at], field=available_at)
    if result[symbol].eq("").any():
        raise ValueError("event table contains empty symbol")
    return result.sort_values([symbol, available_at]).reset_index(drop=True)


def _asof_by_symbol(
    decisions: pd.DataFrame,
    events: pd.DataFrame,
    *,
    prefix: str,
    available_at: str = "available_at",
) -> pd.DataFrame:
    left = decisions.copy()
    if "decision_time" not in left:
        raise ValueError("decisions require decision_time")
    left["decision_time"] = _utc_series(left["decision_time"], field="decision_time")
    if events.empty:
        return left
    right = _prepare_events(events, available_at=available_at)
    value_columns = [column for column in right.columns if column not in {"symbol", available_at}]
    right = right.rename(
        columns={
            available_at: f"{prefix}_available_at",
            **{column: f"{prefix}_{column}" for column in value_columns},
        }
    )
    pieces: list[pd.DataFrame] = []
    for symbol, group in left.groupby("symbol", sort=False):
        source = right.loc[right["symbol"].eq(symbol)].drop(columns=["symbol"]).copy()
        group = group.sort_values("decision_time")
        if source.empty:
            merged = group.copy()
        else:
            merged = pd.merge_asof(
                group,
                source.sort_values(f"{prefix}_available_at"),
                left_on="decision_time",
                right_on=f"{prefix}_available_at",
                direction="backward",
                allow_exact_matches=True,
            )
        pieces.append(merged)
    return pd.concat(pieces, ignore_index=True) if pieces else left.iloc[0:0].copy()


def build_historical_pit_shariah_ledger_v225(
    decisions: pd.DataFrame,
    *,
    financial_events: pd.DataFrame,
    market_cap_events: pd.DataFrame,
    business_events: pd.DataFrame,
    attestation_events: pd.DataFrame,
    policy: PITHistoricalEligibilityPolicyV225 | None = None,
) -> PITHistoricalEligibilityBundleV225:
    """Build a strictly PIT Shariah state for each symbol/decision timestamp.

    Required event semantics:
    - financial_events: raw facts known as of ``available_at``. Expected fields:
      short_debt, long_debt, cash, receivables, report_date, filing_date.
    - market_cap_events: historical/PIT market cap, never today's market cap.
    - business_events: timestamped business classification state.
    - attestation_events: timestamped human/external Shariah attestations.

    Missing evidence fails closed. No current snapshot is backfilled into history.
    """
    active = policy or PITHistoricalEligibilityPolicyV225()
    if decisions.empty:
        audit = {
            "schema": SCHEMA,
            "valid": True,
            "rows": 0,
            "verified_trade_eligible": 0,
            "errors": [],
            "point_in_time": True,
            "execution_authority": AUTHORITY_NONE,
            "broker_calls": 0,
            "order_calls": 0,
        }
        return PITHistoricalEligibilityBundleV225(pd.DataFrame(), audit)
    required = {"symbol", "decision_time"}
    missing = sorted(required.difference(decisions.columns))
    if missing:
        raise ValueError(f"decisions missing columns {missing}")
    left = decisions.copy()
    left["symbol"] = left["symbol"].astype(str).str.upper().str.strip()
    left["decision_time"] = _utc_series(left["decision_time"], field="decision_time")
    left["_order"] = np.arange(len(left))

    joined = _asof_by_symbol(left, financial_events, prefix="financial")
    joined = _asof_by_symbol(joined, market_cap_events, prefix="market_cap")
    joined = _asof_by_symbol(joined, business_events, prefix="business")
    joined = _asof_by_symbol(joined, attestation_events, prefix="attestation")

    rows: list[dict[str, Any]] = []
    future_evidence_rows = 0
    for raw in joined.to_dict(orient="records"):
        blockers: list[str] = []
        decision_time = pd.Timestamp(raw["decision_time"])
        for prefix in ("financial", "market_cap", "business", "attestation"):
            evidence_time = raw.get(f"{prefix}_available_at")
            if evidence_time not in (None, "") and not pd.isna(evidence_time):
                evidence_time = pd.Timestamp(evidence_time)
                if evidence_time > decision_time:
                    future_evidence_rows += 1
                    blockers.append(f"FUTURE_{prefix.upper()}_EVIDENCE")

        market_cap = _number(raw.get("market_cap_market_cap"))
        short_debt = _number(raw.get("financial_short_debt"))
        long_debt = _number(raw.get("financial_long_debt"))
        cash = _number(raw.get("financial_cash"))
        receivables = _number(raw.get("financial_receivables"))
        business_status = str(raw.get("business_business_status") or "UNKNOWN").upper()

        if active.require_business_state and business_status in {"", "UNKNOWN", "NAN", "NONE"}:
            blockers.append("PIT_BUSINESS_CLASSIFICATION_MISSING")
        if "HARD_EXCLUSION" in business_status or business_status in {"INELIGIBLE", "FAIL"}:
            blockers.append("SHARIAH_INELIGIBLE_BUSINESS")
        if active.require_market_cap and (market_cap is None or market_cap <= 0):
            blockers.append("PIT_MARKET_CAP_MISSING")
        if short_debt is None and long_debt is None:
            blockers.append("PIT_DEBT_FACTS_MISSING")
        if cash is None:
            blockers.append("PIT_CASH_FACTS_MISSING")
        if receivables is None:
            blockers.append("PIT_RECEIVABLES_FACTS_MISSING")

        debt_ratio = cash_ratio = receivables_ratio = None
        if not any(code.startswith("PIT_") for code in blockers) and market_cap:
            debt_ratio = (float(short_debt or 0.0) + float(long_debt or 0.0)) / market_cap
            cash_ratio = float(cash) / market_cap
            receivables_ratio = float(receivables) / market_cap
            if debt_ratio > active.debt_to_market_cap_max:
                blockers.append("DEBT_RATIO")
            if cash_ratio > active.cash_to_market_cap_max:
                blockers.append("CASH_RATIO")
            if receivables_ratio > active.receivables_to_market_cap_max:
                blockers.append("RECEIVABLES_RATIO")

        att_status = str(raw.get("attestation_status") or "").upper()
        att_available = raw.get("attestation_available_at")
        att_valid_until = raw.get("attestation_valid_until")
        attestation_valid = att_status in {
            "SHARIAH_COMPLIANT",
            "SHARIAH_ELIGIBLE",
            "SHARIAH_ELIGIBLE_PIT",
            "VERIFIED",
        }
        if attestation_valid and att_available not in (None, "") and not pd.isna(att_available):
            age_days = (decision_time - pd.Timestamp(att_available)).total_seconds() / 86400.0
            if age_days < 0 or age_days > active.maximum_attestation_age_days:
                attestation_valid = False
        if attestation_valid and att_valid_until not in (None, "") and not pd.isna(att_valid_until):
            expires = pd.Timestamp(att_valid_until)
            expires = expires.tz_localize("UTC") if expires.tzinfo is None else expires.tz_convert("UTC")
            if decision_time > expires:
                attestation_valid = False
        if active.require_verified_attestation and not attestation_valid:
            blockers.append("VERIFIED_ATTESTATION_REQUIRED")

        hard_ratio_failure = any(code in {"DEBT_RATIO", "CASH_RATIO", "RECEIVABLES_RATIO"} for code in blockers)
        incomplete = any(code.startswith("PIT_") for code in blockers)
        if "SHARIAH_INELIGIBLE_BUSINESS" in blockers:
            status = "SHARIAH_INELIGIBLE_BUSINESS"
        elif hard_ratio_failure:
            status = "SHARIAH_INELIGIBLE_FINANCIAL_RATIOS"
        elif incomplete:
            status = "SHARIAH_DATA_INCOMPLETE_PIT"
        elif not attestation_valid:
            status = PASS_ATTESTATION_STATUS
        else:
            status = VERIFIED_STATUS
        eligible = status == VERIFIED_STATUS and not any(code.startswith("FUTURE_") for code in blockers)

        evidence_payload = {
            "symbol": raw["symbol"],
            "decision_time": str(decision_time),
            "financial_available_at": str(raw.get("financial_available_at")),
            "market_cap_available_at": str(raw.get("market_cap_available_at")),
            "business_available_at": str(raw.get("business_available_at")),
            "attestation_available_at": str(raw.get("attestation_available_at")),
            "market_cap": market_cap,
            "debt_ratio": debt_ratio,
            "cash_ratio": cash_ratio,
            "receivables_ratio": receivables_ratio,
            "status": status,
        }
        rows.append(
            {
                "symbol": raw["symbol"],
                "decision_time": decision_time,
                "status": status,
                "business_status": business_status,
                "financial_ratio_status": "FAIL" if hard_ratio_failure else ("PASS" if not incomplete else "DATA_INCOMPLETE"),
                "verified_attestation": bool(attestation_valid),
                "trade_eligible": bool(eligible),
                "debt_to_market_cap": debt_ratio,
                "cash_to_market_cap": cash_ratio,
                "receivables_to_market_cap": receivables_ratio,
                "market_cap": market_cap,
                "report_date": raw.get("financial_report_date"),
                "filing_date": raw.get("financial_filing_date"),
                "financial_available_at": raw.get("financial_available_at"),
                "market_cap_available_at": raw.get("market_cap_available_at"),
                "business_available_at": raw.get("business_available_at"),
                "attestation_available_at": raw.get("attestation_available_at"),
                "attestation_valid_until": raw.get("attestation_valid_until"),
                "methodology": raw.get("attestation_methodology"),
                "attestation_source": raw.get("attestation_source"),
                "reason_codes": "|".join(dict.fromkeys(blockers)),
                "evidence_sha256": _canonical_hash(evidence_payload),
                "point_in_time": True,
                "historical_backfill_allowed": False,
                "execution_authority": AUTHORITY_NONE,
                "broker_calls": 0,
                "order_calls": 0,
                "_order": raw.get("_order"),
            }
        )
    ledger = pd.DataFrame(rows).sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)
    errors: list[str] = []
    if future_evidence_rows:
        errors.append("FUTURE_EVIDENCE_EXPOSED")
    if ledger.duplicated(subset=["symbol", "decision_time"]).any():
        errors.append("DUPLICATE_SYMBOL_DECISION")
    audit = {
        "schema": SCHEMA,
        "valid": not errors,
        "rows": int(len(ledger)),
        "symbols": int(ledger["symbol"].nunique()) if not ledger.empty else 0,
        "verified_trade_eligible": int(ledger["trade_eligible"].sum()) if not ledger.empty else 0,
        "pending_attestation": int(ledger["status"].eq(PASS_ATTESTATION_STATUS).sum()) if not ledger.empty else 0,
        "data_incomplete": int(ledger["status"].eq("SHARIAH_DATA_INCOMPLETE_PIT").sum()) if not ledger.empty else 0,
        "future_evidence_rows": int(future_evidence_rows),
        "point_in_time": True,
        "historical_market_cap_required": active.require_market_cap,
        "historical_business_state_required": active.require_business_state,
        "verified_attestation_required": active.require_verified_attestation,
        "historical_backfill_allowed": False,
        "errors": errors,
        "ledger_sha256": _canonical_hash(ledger.to_dict(orient="records")),
        "automatic_attestation": False,
        "automatic_live_promotion": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }
    return PITHistoricalEligibilityBundleV225(ledger=ledger, audit=audit)


def attach_pit_shariah_to_training_frame_v225(
    training: pd.DataFrame,
    ledger: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the latest eligible Shariah state without future leakage."""
    if training.empty:
        return training.copy()
    if not {"symbol", "decision_time"}.issubset(training.columns):
        raise ValueError("training frame requires symbol and decision_time")
    if not {"symbol", "decision_time", "trade_eligible", "status"}.issubset(ledger.columns):
        raise ValueError("Shariah ledger is missing required fields")
    events = ledger.rename(columns={"decision_time": "available_at"}).copy()
    decisions = training.copy()
    decisions["_pit_row"] = np.arange(len(decisions))
    joined = _asof_by_symbol(decisions, events, prefix="shariah")
    known = joined.get("shariah_available_at", pd.Series(index=joined.index, dtype="datetime64[ns, UTC]")).notna()
    decision = pd.to_datetime(joined["decision_time"], utc=True, errors="coerce")
    available = pd.to_datetime(joined.get("shariah_available_at"), utc=True, errors="coerce")
    if (known & (available > decision)).any():
        raise AssertionError("future Shariah state leaked into training frame")
    return joined.sort_values("_pit_row").drop(columns=["_pit_row"]).reset_index(drop=True)


def write_pit_shariah_bundle_v225(
    bundle: PITHistoricalEligibilityBundleV225,
    output_root: str | Path,
) -> Path:
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle.ledger.to_csv(output / "ledger.csv", index=False)
    (output / "audit.json").write_text(
        json.dumps(dict(bundle.audit), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = [
    "PITHistoricalEligibilityPolicyV225",
    "PITHistoricalEligibilityBundleV225",
    "current_verification_to_pit_events_v225",
    "build_attestation_queue_v225",
    "build_historical_pit_shariah_ledger_v225",
    "attach_pit_shariah_to_training_frame_v225",
    "write_pit_shariah_bundle_v225",
]
