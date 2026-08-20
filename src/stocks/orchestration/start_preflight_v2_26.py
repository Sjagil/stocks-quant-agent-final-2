from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import pandas_market_calendars as mcal

from stocks.orchestration.dynamic_shadow_target_book_v2_26 import (
    validate_broker_snapshot_v226,
)

SCHEMA = "operational_start_preflight_v2_26"
AUTHORITY_NONE = "NONE"


def _utc(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    return result.tz_localize("UTC") if result.tzinfo is None else result.tz_convert("UTC")


def expected_latest_closed_nyse_1h_bar_v226(decision_time: datetime | pd.Timestamp) -> pd.Timestamp:
    """Return the start time of the latest NYSE 1h bar actually closed by now."""
    now = _utc(decision_time)
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=(now - pd.Timedelta(days=10)).date(),
        end_date=now.date(),
    )
    candidates: list[pd.Timestamp] = []
    for _, row in schedule.iterrows():
        market_open = _utc(row["market_open"])
        market_close = _utc(row["market_close"])
        start = market_open
        while start < market_close:
            available = min(start + pd.Timedelta(hours=1), market_close)
            if available <= now:
                candidates.append(start)
            start += pd.Timedelta(hours=1)
    if not candidates:
        raise ValueError("NO_CLOSED_NYSE_1H_BAR_AVAILABLE")
    return max(candidates)


def build_start_preflight_v226(
    *,
    decision_time: datetime,
    signals: pd.DataFrame,
    signal_audit: Mapping[str, Any],
    current_shariah_events: pd.DataFrame,
    broker_snapshot: Mapping[str, Any],
    broker_snapshot_max_age_seconds: int = 120,
    shariah_snapshot_max_age_hours: int = 24,
    require_verified_candidate: bool = True,
    require_flat_broker: bool = True,
    require_no_open_orders: bool = True,
) -> dict[str, Any]:
    now = pd.Timestamp(decision_time)
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    blockers: list[str] = []

    if not bool(signal_audit.get("ready")):
        blockers.append("DYNAMIC_SIGNAL_AUDIT_NOT_READY")
    if not bool(signal_audit.get("strict_dynamic_deployment_gate")):
        blockers.append("STRICT_DYNAMIC_DEPLOYMENT_GATE_MISSING")
    if str(signal_audit.get("execution_authority") or "").upper() != AUTHORITY_NONE:
        blockers.append("SIGNAL_EXECUTION_AUTHORITY_PRESENT")
    if int(signal_audit.get("broker_calls", 0) or 0) != 0 or int(signal_audit.get("order_calls", 0) or 0) != 0:
        blockers.append("SIGNAL_BROKER_ACTIVITY_PRESENT")

    expected_bar = expected_latest_closed_nyse_1h_bar_v226(now)
    latest_signal_bar = None
    if signals.empty or "signal_bar_time" not in signals:
        blockers.append("DYNAMIC_SIGNAL_STATE_EMPTY")
    else:
        parsed = pd.to_datetime(signals["signal_bar_time"], utc=True, errors="coerce")
        if parsed.isna().all():
            blockers.append("DYNAMIC_SIGNAL_BAR_TIME_INVALID")
        else:
            latest_signal_bar = parsed.max()
            if latest_signal_bar < expected_bar:
                blockers.append("DYNAMIC_MARKET_DATA_STALE")
            if latest_signal_bar > expected_bar:
                blockers.append("DYNAMIC_SIGNAL_BAR_FROM_FUTURE_SESSION")

    verified_overlap = 0
    latest_shariah_snapshot = None
    if current_shariah_events.empty:
        blockers.append("CURRENT_SHARIAH_STATE_MISSING")
    else:
        if "decision_time" not in current_shariah_events:
            blockers.append("CURRENT_SHARIAH_DECISION_TIME_MISSING")
        else:
            times = pd.to_datetime(current_shariah_events["decision_time"], utc=True, errors="coerce")
            if times.isna().all():
                blockers.append("CURRENT_SHARIAH_DECISION_TIME_INVALID")
            else:
                latest_shariah_snapshot = times.max()
                age_hours = (now - latest_shariah_snapshot).total_seconds() / 3600.0
                if age_hours < -0.01:
                    blockers.append("CURRENT_SHARIAH_STATE_FROM_FUTURE")
                elif age_hours > shariah_snapshot_max_age_hours:
                    blockers.append("CURRENT_SHARIAH_STATE_STALE")
        required = {"symbol", "trade_eligible"}
        if not required.issubset(current_shariah_events.columns):
            blockers.append("CURRENT_SHARIAH_COLUMNS_MISSING")
        elif not signals.empty and "symbol" in signals:
            signal_symbols = set(signals["symbol"].dropna().astype(str).str.upper())
            eligible = current_shariah_events.loc[
                current_shariah_events["trade_eligible"].fillna(False).astype(bool)
            ]
            verified_overlap = int(
                eligible["symbol"].astype(str).str.upper().isin(signal_symbols).sum()
            )
            if require_verified_candidate and verified_overlap < 1:
                blockers.append("NO_SHARIAH_VERIFIED_DYNAMIC_CANDIDATES")

    broker = validate_broker_snapshot_v226(
        broker_snapshot,
        decision_time=now.to_pydatetime(),
        maximum_age_seconds=int(broker_snapshot_max_age_seconds),
    )
    blockers.extend(str(value) for value in broker["blockers"])
    snapshot_root = (
        broker_snapshot.get("snapshot")
        if isinstance(broker_snapshot.get("snapshot"), Mapping)
        else {}
    )
    positions_root = (
        snapshot_root.get("positions")
        if isinstance(snapshot_root.get("positions"), Mapping)
        else {}
    )
    positions = positions_root.get("positions") or []
    nonzero_positions = []
    for row in positions:
        if not isinstance(row, Mapping):
            continue
        try:
            quantity = float(
                row.get("position_quantity")
                if row.get("position_quantity") is not None
                else row.get("quantity", 0.0)
            )
        except (TypeError, ValueError):
            quantity = 0.0
        if abs(quantity) > 1e-12:
            nonzero_positions.append(str(row.get("symbol") or "UNKNOWN").upper())
    if require_flat_broker and nonzero_positions:
        blockers.append(
            "INITIAL_SHADOW_REQUIRES_FLAT_BROKER:"
            + ",".join(sorted(set(nonzero_positions)))
        )
    orders_root = (
        snapshot_root.get("all_api_open_orders")
        if isinstance(snapshot_root.get("all_api_open_orders"), Mapping)
        else {}
    )
    if require_no_open_orders and (orders_root.get("open_orders") or []):
        blockers.append("INITIAL_SHADOW_REQUIRES_NO_OPEN_ORDERS")
    blockers = list(dict.fromkeys(blockers))

    return {
        "schema": SCHEMA,
        "start_ready": not blockers,
        "blockers": blockers,
        "decision_time": now.isoformat(),
        "expected_latest_closed_1h_bar": expected_bar.isoformat(),
        "latest_dynamic_signal_bar": (
            latest_signal_bar.isoformat() if latest_signal_bar is not None else None
        ),
        "latest_shariah_snapshot": (
            latest_shariah_snapshot.isoformat() if latest_shariah_snapshot is not None else None
        ),
        "shariah_verified_dynamic_candidates": verified_overlap,
        "broker_snapshot_valid": bool(broker["valid"]),
        "broker_snapshot_captured_at": (
            broker["captured_at"].isoformat() if broker["captured_at"] else None
        ),
        "strict_dynamic_deployment_gate": True,
        "market_session_aware_freshness": True,
        "automatic_attestation": False,
        "broker_submission_enabled": False,
        "automatic_live_promotion": False,
        "execution_authority": AUTHORITY_NONE,
        "broker_calls": 0,
        "order_calls": 0,
    }


def build_start_preflight_from_project_v226(
    project_root: str | Path,
    *,
    decision_time: datetime,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    signal_root = root / "artifacts/research_runtime/dynamic_validated_forward_signal_state_v2_24"
    shariah_path = root / "artifacts/research_runtime/pit_shariah_eligibility_v2_25/current/current_events.csv"
    broker_path = root / "artifacts/research_runtime/ibkr_readonly_v2_9/snapshot.json"
    config_path = root / "config/pit_shariah_portfolio_v2_25_26.json"
    for path in (signal_root / "signals.csv", signal_root / "audit.json", shariah_path, broker_path, config_path):
        if not path.is_file():
            return {
                "schema": SCHEMA,
                "start_ready": False,
                "blockers": [f"MISSING_ARTIFACT:{path.relative_to(root)}"],
                "execution_authority": AUTHORITY_NONE,
                "broker_calls": 0,
                "order_calls": 0,
            }
    signals = pd.read_csv(signal_root / "signals.csv", dtype={"hypothesis_id": str})
    signal_audit = json.loads((signal_root / "audit.json").read_text(encoding="utf-8"))
    shariah = pd.read_csv(shariah_path)
    broker = json.loads(broker_path.read_text(encoding="utf-8"))
    if not any(broker.get(key) for key in ("captured_at", "snapshot_time", "timestamp")):
        broker["captured_at"] = datetime.fromtimestamp(broker_path.stat().st_mtime, tz=UTC).isoformat()
    config = json.loads(config_path.read_text(encoding="utf-8"))["preflight"]
    return build_start_preflight_v226(
        decision_time=decision_time,
        signals=signals,
        signal_audit=signal_audit,
        current_shariah_events=shariah,
        broker_snapshot=broker,
        broker_snapshot_max_age_seconds=int(config["broker_snapshot_max_age_seconds"]),
        shariah_snapshot_max_age_hours=int(config["shariah_snapshot_max_age_hours"]),
        require_verified_candidate=bool(config["require_at_least_one_verified_candidate"]),
        require_flat_broker=bool(config["require_flat_broker_for_initial_shadow"]),
        require_no_open_orders=bool(config["require_no_open_orders"]),
    )


__all__ = [
    "expected_latest_closed_nyse_1h_bar_v226",
    "build_start_preflight_v226",
    "build_start_preflight_from_project_v226",
]
