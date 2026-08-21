from __future__ import annotations

import json
import os
import time
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from _common import (
    add_repo_src,
    artifact_ref,
    base_health,
    run_worker,
)


CAPABILITIES = (
    "health",
    "broker_snapshot_read_only",
    "historical_bars_read_only",
)


@dataclass(frozen=True)
class ObserverConfig:
    env_file: Path
    host: str
    port: int
    primary_client_id: int
    recon_client_id: int
    account_fingerprint_key: str
    request_timeout_seconds: float
    commission_grace_seconds: float
    snapshot_stability_delay_seconds: float
    read_only: bool = True
    live_trading_enabled: bool = False
    allow_order_transmission: bool = False
    execution_authority: str = "NONE"


def _repo(request: dict[str, Any]) -> Path:
    value = (request.get("context") or {}).get("repo_path")
    if not value:
        raise ValueError("reference repo_path missing")

    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)

    return path


def _project_root(request: dict[str, Any]) -> Path:
    value = (request.get("context") or {}).get("project_root")
    if not value:
        raise ValueError("project_root missing")

    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)

    return path


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name}_REQUIRED")
    return value


def _positive_int(name: str) -> int:
    raw = _required_env(name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name}_INVALID") from exc

    if value <= 0:
        raise ValueError(f"{name}_MUST_BE_POSITIVE")

    return value


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return float(default)

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name}_INVALID") from exc

    if value <= 0:
        raise ValueError(f"{name}_MUST_BE_POSITIVE")

    return value


def observer_settings() -> dict[str, Any]:
    host = _required_env("IBKR_HOST")
    port = _positive_int("IBKR_PORT")
    primary = _positive_int("IBKR_CLIENT_ID")
    recon = _positive_int("IBKR_RECON_CLIENT_ID")
    fingerprint = _required_env(
        "IBKR_ACCOUNT_FINGERPRINT_KEY"
    )
    base = os.environ.get(
        "IBKR_ACCOUNT_BASE_CURRENCY",
        "EUR",
    ).strip().upper()

    if primary == 0 or recon == 0:
        raise ValueError("CLIENT_ID_ZERO_BLOCKED")

    if primary == recon:
        raise ValueError("CLIENT_ID_COLLISION_BLOCKED")

    if base != "EUR":
        raise ValueError(
            "V2_9_REQUIRES_EUR_BASE_CURRENCY"
        )

    return {
        "host": host,
        "port": port,
        "primary_client_id": primary,
        "recon_client_id": recon,
        "account_fingerprint_key": fingerprint,
        "base_currency": base,
        "request_timeout_seconds": _float_env(
            "IBKR_RECON_REQUEST_TIMEOUT_SECONDS",
            15.0,
        ),
        "commission_grace_seconds": _float_env(
            "IBKR_RECON_COMMISSION_GRACE_SECONDS",
            1.0,
        ),
        "snapshot_stability_delay_seconds": _float_env(
            "IBKR_RECON_SNAPSHOT_STABILITY_DELAY_SECONDS",
            1.0,
        ),
    }


def _health(request: dict[str, Any]) -> dict[str, Any]:
    repo = _repo(request)
    add_repo_src(repo)

    result = base_health(
        request,
        distributions=("ibapi", "filelock"),
        imports=(
            "ibapi",
            "stocks.ibkr.reconciliation.adapter",
            "stocks.ibkr.reconciliation.snapshots",
            "stocks.ibkr.reconciliation.account_state",
        ),
        capabilities=CAPABILITIES,
    )

    try:
        safe = observer_settings()
        result.setdefault("data", {})[
            "observer_config"
        ] = {
            "host_configured": bool(safe["host"]),
            "port": safe["port"],
            "primary_client_id_nonzero": (
                safe["primary_client_id"] != 0
            ),
            "recon_client_id_nonzero": (
                safe["recon_client_id"] != 0
            ),
            "client_ids_distinct": (
                safe["primary_client_id"]
                != safe["recon_client_id"]
            ),
            "fingerprint_key_configured": True,
            "base_currency": safe["base_currency"],
            "broker_writes_enabled": False,
        }
    except Exception as exc:
        result["state"] = "DEGRADED"
        result.setdefault("warnings", []).append(
            f"{type(exc).__name__}: {exc}"
        )

    return result


def _sum_counters(
    left: dict[str, int],
    right: dict[str, int],
) -> dict[str, int]:
    keys = set(left) | set(right)
    return {
        key: int(left.get(key, 0))
        + int(right.get(key, 0))
        for key in sorted(keys)
    }


def _snapshot(request: dict[str, Any], artifact_dir: Path):
    repo = _repo(request)
    project_root = _project_root(request)
    add_repo_src(repo)

    from stocks.ibkr.reconciliation.account_state import (
        derive_economic_account_state,
    )
    from stocks.ibkr.reconciliation.models import (
        model_to_jsonable,
    )
    from stocks.ibkr.reconciliation.snapshots import (
        capture_snapshot,
        snapshot_components_complete,
        stability_status,
    )

    settings = observer_settings()

    config = ObserverConfig(
        env_file=project_root / ".env",
        host=settings["host"],
        port=settings["port"],
        primary_client_id=settings[
            "primary_client_id"
        ],
        recon_client_id=settings[
            "recon_client_id"
        ],
        account_fingerprint_key=settings[
            "account_fingerprint_key"
        ],
        request_timeout_seconds=settings[
            "request_timeout_seconds"
        ],
        commission_grace_seconds=settings[
            "commission_grace_seconds"
        ],
        snapshot_stability_delay_seconds=settings[
            "snapshot_stability_delay_seconds"
        ],
    )

    first, read_1, write_1 = capture_snapshot(config)

    time.sleep(
        config.snapshot_stability_delay_seconds
    )

    second, read_2, write_2 = capture_snapshot(config)

    stability = stability_status(first, second)
    snapshot = model_to_jsonable(second)

    economic = derive_economic_account_state(
        snapshot,
        expected_base_currency=settings[
            "base_currency"
        ],
        snapshot_hash_verified=bool(
            second.content_hash
        ),
        execution_max_age=timedelta(
            seconds=float(
                os.environ.get(
                    "IBKR_EXECUTION_STATE_MAX_AGE_SECONDS",
                    "120",
                )
            )
        ),
    )

    complete = snapshot_components_complete(second)
    stable = bool(stability.get("stable", False))

    if not stable:
        blockers = list(
            economic.get("execution_blockers") or []
        )
        blockers.append(
            "BROKER_DOUBLE_SNAPSHOT_NOT_STABLE"
        )
        economic["execution_blockers"] = sorted(
            set(blockers)
        )
        economic["execution_status"] = "NO_GO"

    reads = _sum_counters(read_1, read_2)
    writes = _sum_counters(write_1, write_2)

    write_total = sum(
        int(value)
        for key, value in writes.items()
        if key.endswith("_calls")
    )

    if write_total != 0:
        raise RuntimeError(
            "BROKER_WRITE_COUNTER_NONZERO_BLOCKED"
        )

    payload = {
        "schema": "ibkr_readonly_snapshot_v2_9",
        "broker_observation_authority": (
            "READ_ONLY_OBSERVATION"
        ),
        "execution_authority": "NONE",
        "snapshot_components_complete": complete,
        "double_snapshot_stable": stable,
        "stability": stability,
        "economic_account_state": economic,
        "snapshot": snapshot,
        "read_counters": reads,
        "write_counters": writes,
        "broker_write_calls": write_total,
        "config": {
            "host": settings["host"],
            "port": settings["port"],
            "primary_client_id_nonzero": True,
            "recon_client_id_nonzero": True,
            "client_ids_distinct": True,
            "account_fingerprint_key_configured": True,
            "base_currency": settings[
                "base_currency"
            ],
            "read_only": True,
            "live_trading_enabled_by_worker": False,
            "allow_order_transmission_by_worker": False,
        },
    }

    output = (
        artifact_dir
        / "ibkr_readonly_snapshot_v2_9.json"
    )
    output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    state = (
        "OK"
        if complete and stable
        else "DEGRADED"
    )

    return {
        "state": state,
        "data": {
            "snapshot_components_complete": complete,
            "double_snapshot_stable": stable,
            "lifecycle_state": economic.get(
                "lifecycle_state"
            ),
            "research_status": economic.get(
                "research_status"
            ),
            "execution_account_status": economic.get(
                "execution_status"
            ),
            "reporting_value_eur": economic.get(
                "reporting_value_eur"
            ),
            "spendable_eur": economic.get(
                "spendable_eur"
            ),
            "execution_sizing_capacity_eur": economic.get(
                "execution_sizing_capacity_eur"
            ),
            "broker_write_calls": write_total,
            "execution_authority": "NONE",
        },
        "artifacts": [
            artifact_ref(
                output,
                media_type="application/json",
            )
        ],
        "warnings": (
            []
            if complete and stable
            else [
                "BROKER_SNAPSHOT_NOT_EXECUTION_STABLE"
            ]
        ),
    }



@dataclass
class HistoricalBarsState:
    ready: threading.Event = field(default_factory=threading.Event)
    done: dict[int, threading.Event] = field(default_factory=dict)
    bars: dict[int, list[Any]] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    historical_data_calls: int = 0
    historical_cancel_calls: int = 0
    financial_calls: dict[str, int] = field(
        default_factory=lambda: {
            "place_order": 0,
            "cancel_order": 0,
            "global_cancel": 0,
        }
    )
    lock: threading.RLock = field(default_factory=threading.RLock)

    def event(self, request_id: int) -> threading.Event:
        with self.lock:
            return self.done.setdefault(request_id, threading.Event())


def _historical_bars_read_only(
    request: dict[str, Any],
    artifact_dir: Path,
) -> dict[str, Any]:
    repo = _repo(request)
    add_repo_src(repo)

    from ibapi.client import EClient
    from ibapi.contract import Contract
    from ibapi.wrapper import EWrapper

    settings = observer_settings()
    payload = request.get("payload") or {}
    symbols: list[str] = []
    for value in payload.get("symbols") or []:
        symbol = str(value).strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    if not symbols:
        raise ValueError("HISTORICAL_SYMBOLS_REQUIRED")
    if len(symbols) > 25:
        raise ValueError("HISTORICAL_SYMBOL_LIMIT_EXCEEDED")

    duration = str(payload.get("duration") or "5 D")
    bar_size = str(payload.get("bar_size") or "30 mins")
    what_to_show = str(payload.get("what_to_show") or "TRADES").upper()
    use_rth = bool(payload.get("use_rth", True))
    keep_up_to_date = bool(payload.get("keep_up_to_date", False))
    if keep_up_to_date:
        raise ValueError("KEEP_UP_TO_DATE_BLOCKED_FOR_V2_27")
    if bar_size != "30 mins":
        raise ValueError("V2_27_REQUIRES_30_MIN_SOURCE_BARS")
    if what_to_show != "TRADES":
        raise ValueError("V2_27_REQUIRES_TRADES")

    raw_client_id = os.environ.get("IBKR_MARKET_DATA_CLIENT_ID", "").strip()
    client_id = int(raw_client_id) if raw_client_id else int(settings["recon_client_id"]) + 2000
    if client_id in {int(settings["primary_client_id"]), int(settings["recon_client_id"]), 0}:
        raise ValueError("MARKET_DATA_CLIENT_ID_COLLISION")

    timeout = _float_env("IBKR_HISTORICAL_REQUEST_TIMEOUT_SECONDS", 20.0)
    spacing = _float_env("IBKR_HISTORICAL_REQUEST_SPACING_SECONDS", 0.25)
    state = HistoricalBarsState()

    class App(EWrapper, EClient):  # type: ignore[misc]
        def __init__(self):
            EClient.__init__(self, self)

        def nextValidId(self, orderId: int) -> None:  # noqa: N802
            state.ready.set()

        def historicalData(self, reqId: int, bar: Any) -> None:  # noqa: N802
            with state.lock:
                state.bars.setdefault(reqId, []).append(bar)

        def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:  # noqa: N802
            state.event(reqId).set()

        def error(self, reqId: Any, errorCode: Any, errorString: Any, *args: Any) -> None:  # type: ignore[override]
            try:
                code = int(errorCode)
            except Exception:
                code = -1
            with state.lock:
                state.errors.append(
                    {"request_id": reqId, "code": code, "message": str(errorString)}
                )

    app = App()
    thread = None
    records: dict[str, list[dict[str, Any]]] = {}
    symbol_results: dict[str, dict[str, Any]] = {}

    def parse_timestamp(value: Any) -> str:
        raw = str(value).strip()
        if raw.replace(".", "", 1).isdigit():
            return datetime.fromtimestamp(int(float(raw)), tz=UTC).isoformat()
        from pandas import Timestamp
        stamp = Timestamp(raw)
        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
        return stamp.isoformat()

    try:
        app.connect(settings["host"], int(settings["port"]), client_id)
        thread = threading.Thread(target=app.run, name="ibkr-market-data-v2-27", daemon=True)
        thread.start()
        if not state.ready.wait(timeout):
            raise TimeoutError("IBKR_HISTORICAL_HANDSHAKE_TIMEOUT")

        for index, symbol in enumerate(symbols):
            req_id = 27000 + index
            event = state.event(req_id)
            event.clear()
            with state.lock:
                state.bars[req_id] = []

            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            state.historical_data_calls += 1
            app.reqHistoricalData(
                req_id,
                contract,
                "",
                duration,
                bar_size,
                what_to_show,
                1 if use_rth else 0,
                2,
                False,
                [],
            )
            if not event.wait(timeout):
                state.historical_cancel_calls += 1
                app.cancelHistoricalData(req_id)
                symbol_results[symbol] = {"status": "ERROR", "reason": "CALLBACK_TIMEOUT"}
                continue

            request_errors = [
                row
                for row in state.errors
                if str(row.get("request_id")) == str(req_id)
                and int(row.get("code", -1)) not in {2104, 2106, 2107, 2108, 2158}
            ]
            parsed: list[dict[str, Any]] = []
            for bar in list(state.bars.get(req_id, [])):
                parsed.append(
                    {
                        "timestamp": parse_timestamp(getattr(bar, "date")),
                        "open": float(getattr(bar, "open")),
                        "high": float(getattr(bar, "high")),
                        "low": float(getattr(bar, "low")),
                        "close": float(getattr(bar, "close")),
                        "volume": float(getattr(bar, "volume")),
                        "bar_count": int(getattr(bar, "barCount", 0) or 0),
                        "source": "IBKR_TWS_API",
                    }
                )
            records[symbol] = parsed
            symbol_results[symbol] = {
                "status": "OK" if parsed and not request_errors else "ERROR",
                "rows": len(parsed),
                "errors": request_errors,
            }
            if index + 1 < len(symbols):
                time.sleep(spacing)
    finally:
        try:
            app.disconnect()
        finally:
            if thread is not None:
                thread.join(timeout=2.0)

    write_total = sum(int(v) for v in state.financial_calls.values())
    if write_total != 0:
        raise RuntimeError("BROKER_WRITE_COUNTER_NONZERO_BLOCKED")

    output_payload = {
        "schema": "ibkr_historical_bars_read_only_v2_27",
        "captured_at": datetime.now(UTC).isoformat(),
        "symbols": symbols,
        "duration": duration,
        "bar_size": bar_size,
        "what_to_show": what_to_show,
        "use_rth": use_rth,
        "keep_up_to_date": False,
        "format_date": 2,
        "records": records,
        "symbol_results": symbol_results,
        "historical_data_calls": state.historical_data_calls,
        "historical_cancel_calls": state.historical_cancel_calls,
        "financial_calls": state.financial_calls,
        "broker_write_calls": write_total,
        "order_calls": 0,
        "execution_authority": "NONE",
        "market_data_authority": "READ_ONLY",
        "client_id_nonzero": client_id != 0,
        "client_id_distinct": True,
    }
    output = artifact_dir / "ibkr_historical_bars_read_only_v2_27.json"
    output.write_text(
        json.dumps(output_payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    ok_count = sum(1 for row in symbol_results.values() if row.get("status") == "OK")
    return {
        "state": "OK" if ok_count == len(symbols) else "DEGRADED",
        "data": {
            "symbols": len(symbols),
            "ok_symbols": ok_count,
            "historical_data_calls": state.historical_data_calls,
            "broker_write_calls": 0,
            "order_calls": 0,
            "execution_authority": "NONE",
            "market_data_authority": "READ_ONLY",
        },
        "artifacts": [artifact_ref(output, media_type="application/json")],
        "warnings": [] if ok_count == len(symbols) else ["SOME_IBKR_HISTORICAL_SYMBOLS_FAILED"],
    }

def handle(
    request: dict[str, Any],
    artifact_dir: Path,
) -> dict[str, Any]:
    action = request.get("action")

    if action == "health":
        return _health(request)

    if action == "broker_snapshot_read_only":
        return _snapshot(
            request,
            artifact_dir,
        )

    if action == "historical_bars_read_only":
        return _historical_bars_read_only(
            request,
            artifact_dir,
        )

    raise ValueError(
        f"unsupported action: {action}"
    )


if __name__ == "__main__":
    run_worker(handle)
