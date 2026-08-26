from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pandas_market_calendars as mcal

from .authority_v2_41 import authority_status
from .contracts_v2_41 import BrokerSnapshot, PreflightReport, ExecutionMode
from .freshness_v2_41 import check_file_freshness
from .reconciliation_v2_41 import reconcile
from .state_store_v2_41 import ProductionStoreV241


def _market_open(now: pd.Timestamp, calendar_name: str) -> bool:
    cal = mcal.get_calendar(calendar_name)
    now = pd.Timestamp(now)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    schedule = cal.schedule(
        start_date=(now - pd.Timedelta(days=2)).date().isoformat(),
        end_date=(now + pd.Timedelta(days=1)).date().isoformat(),
    )
    if schedule.empty:
        return False
    opens = pd.to_datetime(schedule["market_open"], utc=True)
    closes = pd.to_datetime(schedule["market_close"], utc=True)
    return bool(((opens <= now) & (now <= closes)).any())


def _broker_clock_drift_seconds(current_time: str, now: pd.Timestamp) -> float:
    try:
        broker_time = pd.Timestamp(current_time)
        if broker_time.tzinfo is None:
            broker_time = broker_time.tz_localize("UTC")
        else:
            broker_time = broker_time.tz_convert("UTC")
        return abs(float((broker_time - now).total_seconds()))
    except Exception:
        return float("inf")


def build_preflight(
    *,
    root: str | Path,
    cfg: dict[str, Any],
    store: ProductionStoreV241,
    snapshot: BrokerSnapshot,
    relevant_symbols: set[str] | None = None,
    now: pd.Timestamp | None = None,
) -> PreflightReport:
    root = Path(root).resolve()
    now_ts = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if now_ts.tzinfo is None:
        now_ts = now_ts.tz_localize("UTC")
    else:
        now_ts = now_ts.tz_convert("UTC")

    authority = authority_status(root, cfg, store)
    mode = ExecutionMode(authority.mode)
    recon = reconcile(store, snapshot.positions, snapshot.open_orders)

    symbols = sorted({str(s).upper() for s in (relevant_symbols or set()) if str(s).strip()})
    freshness = {}
    for symbol in symbols:
        path = root / cfg["data"]["provider_root"] / f"{symbol}_{cfg['data']['timeframe']}.parquet"
        freshness[symbol] = check_file_freshness(
            symbol,
            path,
            now=now_ts,
            calendar_name=cfg["data"].get("market_calendar", "NYSE"),
            tolerance_minutes=float(cfg["data"].get("freshness_tolerance_minutes", 150)),
        ).to_dict()

    fresh_pass = all(bool(row["passed"]) for row in freshness.values()) if freshness else True
    date_utc = now_ts.date().isoformat()
    opening = store.opening_equity(date_utc, snapshot.net_liquidation)
    drawdown = 0.0 if opening <= 0 else max(0.0, 1.0 - float(snapshot.net_liquidation) / float(opening))
    max_dd = float(cfg["risk"]["max_daily_net_liq_drawdown_fraction"])
    orders_today = store.orders_today(date_utc)
    market_open = _market_open(now_ts, cfg["data"].get("market_calendar", "NYSE"))
    broker_clock_drift = _broker_clock_drift_seconds(snapshot.current_time, now_ts)
    max_clock_drift = float(cfg["runtime"].get("maximum_broker_clock_drift_seconds", 10))

    mode_env_ok = (
        True if mode == ExecutionMode.OBSERVE
        else snapshot.environment == ("PAPER" if mode == ExecutionMode.PAPER else "LIVE")
    )
    submission_env_ok = (
        not authority.submission_enabled
        or authority.submission_environment == snapshot.environment
    )
    live_specific_ok = (
        True if mode != ExecutionMode.LIVE_CANARY
        else bool(authority.live_armed)
        and float(cfg["risk"].get("max_live_canary_notional_eur", 0) or 0) > 0
    )
    mode_submission_ok = (
        True if mode == ExecutionMode.OBSERVE
        else bool(authority.submission_enabled)
    )

    gates = {
        "BROKER_CONNECTED": bool(snapshot.connected),
        "BROKER_ACCOUNT_IDENTIFIED": bool(snapshot.account),
        "BROKER_ACCOUNT_EQUITY_POSITIVE": float(snapshot.net_liquidation) > 0,
        "READONLY_BROKER_WRITE_CALLS_ZERO": int(snapshot.broker_write_calls) == 0,
        "BROKER_CLOCK_SYNC": broker_clock_drift <= max_clock_drift,
        "BASELINE_ADOPTED": bool(store.get("baseline_adopted", False)),
        "RECONCILIATION_PASS": bool(recon.get("passed")),
        "DATA_FRESH": fresh_pass,
        "KILL_SWITCH_CLEAR": not authority.kill_switch_active,
        "DAILY_DRAWDOWN_WITHIN_LIMIT": drawdown < max_dd,
        "DAILY_ORDER_CAP_AVAILABLE": orders_today < int(cfg["risk"]["max_new_orders_per_day"]),
        "MODE_BROKER_ENVIRONMENT_MATCH": mode_env_ok,
        "SUBMISSION_ENVIRONMENT_MATCH": submission_env_ok,
        "MODE_SUBMISSION_ENABLED": mode_submission_ok,
        "LIVE_CANARY_ARM_AND_CAP_READY": live_specific_ok,
        "LIVE_CANARY_BASE_CURRENCY_EUR": (True if mode != ExecutionMode.LIVE_CANARY else str(snapshot.base_currency).upper() == "EUR"),
        "RTH_OPEN": (market_open if cfg["risk"].get("regular_trading_hours_only", True) and mode != ExecutionMode.OBSERVE else True),
        "RL_DIRECT_BROKER_CONTROL_DISABLED": not bool(cfg["eligibility"].get("allow_rl_direct_broker_control", False)),
        "AUTOMATIC_LIVE_PROMOTION_DISABLED": not bool(cfg["authority"].get("automatic_live_promotion", False)),
        "AUTOMATIC_CHAMPION_PROMOTION_DISABLED": not bool(cfg["authority"].get("automatic_champion_promotion", False)),
    }

    blockers = tuple(name for name, ok in gates.items() if not ok)
    warnings = []
    if mode == ExecutionMode.OBSERVE:
        warnings.append("OBSERVE_MODE_NO_BROKER_WRITES")
    if not symbols:
        warnings.append("NO_RELEVANT_SYMBOLS")

    return PreflightReport(
        passed=not blockers,
        mode=mode.value,
        gates=gates,
        blockers=blockers,
        warnings=tuple(warnings),
        diagnostics={
            "authority": authority.to_dict(),
            "reconciliation": recon,
            "freshness": freshness,
            "daily_opening_net_liquidation": opening,
            "current_net_liquidation": snapshot.net_liquidation,
            "daily_drawdown_fraction": drawdown,
            "daily_drawdown_limit_fraction": max_dd,
            "orders_today": orders_today,
            "market_open": market_open,
            "broker_environment": snapshot.environment,
            "broker_write_calls_preflight": snapshot.broker_write_calls,
            "broker_clock_drift_seconds": broker_clock_drift,
            "maximum_broker_clock_drift_seconds": max_clock_drift,
            "checked_at": now_ts.isoformat(),
        },
    )
