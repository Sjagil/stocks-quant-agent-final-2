from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env

from .contracts_v2_41 import BrokerSnapshot


def _float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, dict):
        value = value.get("amount", value.get("value"))
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if math.isfinite(result) else float(default)


def _utc(value: Any) -> str:
    try:
        stamp = pd.Timestamp(value)
        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
        return stamp.isoformat()
    except Exception:
        return pd.Timestamp.now(tz="UTC").isoformat()


@dataclass(frozen=True)
class ReferenceBrokerSnapshotV2431:
    snapshot: BrokerSnapshot | None
    healthy: bool
    blockers: tuple[str, ...]
    diagnostics: dict[str, Any]
    artifact_path: str | None
    execution_authority: str = "NONE"


def _positions(raw_snapshot: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in raw_snapshot.get("positions", {}).get("positions", []) or []:
        if str(row.get("security_type", "")).upper() != "STK":
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        out[symbol] = out.get(symbol, 0.0) + _float(row.get("position_quantity"))
    return out


def _orders(raw_snapshot: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = raw_snapshot.get("all_api_open_orders", {}).get("open_orders", []) or []
    out = []
    for row in rows:
        out.append({
            "order_id": int(_float(row.get("broker_order_id"), 0)),
            "perm_id": int(_float(row.get("perm_id"), 0)),
            "parent_id": int(_float(row.get("parent_id"), 0)),
            "order_ref": str(row.get("order_ref_hash") or ""),
            "action": str(row.get("action") or ""),
            "quantity": _float(row.get("total_quantity")),
            "order_type": str(row.get("order_type") or ""),
            "status": str(row.get("order_status") or ""),
            "symbol": str(row.get("symbol") or "").upper(),
        })
    return tuple(out)


def _fills(raw_snapshot: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    out = []
    for row in raw_snapshot.get("executions", {}).get("executions", []) or []:
        out.append({
            "exec_id": str(row.get("execution_id") or ""),
            "broker_order_id": int(_float(row.get("broker_order_id"), 0)),
            "order_ref": str(row.get("order_ref_hash") or ""),
            "symbol": str(row.get("symbol") or "").upper(),
            "side": str(row.get("side") or ""),
            "shares": _float(row.get("quantity")),
            "price": _float(row.get("price")),
            "filled_at": _utc(row.get("execution_time")),
        })
    return tuple(out)


def _account_fingerprint(raw_snapshot: dict[str, Any]) -> str:
    """Return the unique non-ledger IBKR account fingerprint.

    Ledger rows are deliberately excluded because IBKR can expose synthetic
    ledger scopes which must not be interpreted as additional broker accounts.
    This mirrors references/Stocks economic-account identity semantics.
    """
    fingerprints = sorted({
        str(row.get("account_fingerprint"))
        for row in raw_snapshot.get("account", {}).get("values", []) or []
        if row.get("account_fingerprint")
        and not str(row.get("tag") or "").startswith("$LEDGER-")
    })
    return f"FP:{fingerprints[0]}" if len(fingerprints) == 1 else ""


def fetch_reference_broker_snapshot_v2431(
    project_root: str | Path,
    *,
    integration: str = "stocks_ibkr_reference",
    timeout_seconds: int = 90,
    require_double_snapshot_stable: bool = True,
) -> ReferenceBrokerSnapshotV2431:
    """Use the imported Stocks native-ibapi reconciliation stack for read-only preflight.

    Unlike the legacy ib_async connection, this path records partial callback status
    instead of turning synchronization timeouts into an opaque connection exception.
    It never grants execution authority and rejects any non-zero write counter.
    """
    root = Path(project_root).resolve()
    load_project_env(root)
    registry = IntegrationRegistry.load(root / "config/integrations.yaml", project_root=root)
    runner = IntegrationRunner(registry)
    started = time.monotonic()
    try:
        response = runner.run(
            integration,
            "broker_snapshot_read_only",
            {},
            timeout_seconds=int(timeout_seconds),
        )
    except Exception as exc:
        return ReferenceBrokerSnapshotV2431(
            snapshot=None,
            healthy=False,
            blockers=("IBKR_REFERENCE_SNAPSHOT_EXCEPTION",),
            diagnostics={
                "error": f"{type(exc).__name__}:{exc}",
                "elapsed_seconds": round(time.monotonic() - started, 4),
            },
            artifact_path=None,
        )

    diagnostics: dict[str, Any] = {
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "response_ok": bool(response.ok),
        "response_state": str(getattr(getattr(response, "state", None), "value", getattr(response, "state", "UNKNOWN"))),
        "response_error": str(response.error or ""),
    }
    if not response.artifacts:
        return ReferenceBrokerSnapshotV2431(
            snapshot=None,
            healthy=False,
            blockers=("IBKR_REFERENCE_SNAPSHOT_ARTIFACT_MISSING",),
            diagnostics=diagnostics,
            artifact_path=None,
        )

    artifact = Path(response.artifacts[0].path)
    diagnostics["artifact"] = str(artifact)
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except Exception as exc:
        diagnostics["parse_error"] = f"{type(exc).__name__}:{exc}"
        return ReferenceBrokerSnapshotV2431(
            snapshot=None,
            healthy=False,
            blockers=("IBKR_REFERENCE_SNAPSHOT_PARSE_FAILED",),
            diagnostics=diagnostics,
            artifact_path=str(artifact),
        )

    write_calls = int(payload.get("broker_write_calls", 0))
    if write_calls != 0:
        raise RuntimeError("IBKR_REFERENCE_SNAPSHOT_RECORDED_WRITE_CALLS")

    raw = dict(payload.get("snapshot") or {})
    economic = dict(payload.get("economic_account_state") or {})
    complete = bool(payload.get("snapshot_components_complete"))
    stable = bool(payload.get("double_snapshot_stable"))
    lifecycle = str(economic.get("lifecycle_state") or "UNKNOWN")
    execution_status = str(economic.get("execution_status") or "NO_GO")
    research_status = str(economic.get("research_status") or "NO_GO")

    blockers: list[str] = []
    if not response.ok:
        blockers.append("IBKR_REFERENCE_INTEGRATION_NOT_OK")
    if not complete:
        blockers.append("IBKR_REFERENCE_SNAPSHOT_INCOMPLETE")
    if require_double_snapshot_stable and not stable:
        blockers.append("IBKR_REFERENCE_SNAPSHOT_UNSTABLE")
    if lifecycle not in {"ACCOUNT_READY", "CONNECTED"}:
        blockers.append("IBKR_ACCOUNT_NOT_READY")
    if research_status != "RESEARCH_READY":
        blockers.append("IBKR_RESEARCH_ACCOUNT_NOT_READY")
    blockers.extend(str(x) for x in economic.get("execution_blockers", []) or [])

    account = _account_fingerprint(raw)
    if not account:
        blockers.append("IBKR_ACCOUNT_FINGERPRINT_NOT_UNIQUE")

    net_liquidation = _float(economic.get("reporting_value_eur"))
    if net_liquidation <= 0:
        net_liquidation = _float(economic.get("net_liquidation"))
    available_funds = _float(economic.get("available_funds"))
    total_cash = _float(economic.get("reporting_cash_eur"))
    if total_cash == 0:
        total_cash = _float(economic.get("research_sizing_capacity_eur"))
    base = str(economic.get("account_base_currency") or "").upper()
    if not base:
        blockers.append("IBKR_BASE_CURRENCY_UNKNOWN")

    environment = "PAPER"
    # The read-only donor does not expose a raw account id or trading authority.
    # Environment comes only from the configured TWS port convention and is used
    # for main-runtime preflight compatibility, never to authorize an order.
    try:
        port = int(__import__("os").environ.get("IBKR_PORT", "7497"))
        environment = "LIVE" if port in {7496, 4001} else "PAPER"
    except Exception:
        pass

    snapshot = BrokerSnapshot(
        connected=bool(raw.get("server_version") or payload.get("snapshot_components_complete")),
        account=account,
        environment=environment,
        net_liquidation=net_liquidation,
        available_funds=available_funds,
        total_cash=total_cash,
        base_currency=base or "UNKNOWN",
        positions=_positions(raw),
        open_orders=_orders(raw),
        fills=_fills(raw),
        current_time=_utc(raw.get("snapshot_completed_at") or payload.get("captured_at")),
        broker_write_calls=0,
    )

    diagnostics.update({
        "snapshot_components_complete": complete,
        "double_snapshot_stable": stable,
        "lifecycle_state": lifecycle,
        "research_status": research_status,
        "execution_account_status": execution_status,
        "economic_execution_blockers": list(economic.get("execution_blockers", []) or []),
        "broker_write_calls": write_calls,
        "raw_account_id_stored": False,
    })
    healthy = not blockers and snapshot.connected and snapshot.net_liquidation > 0
    return ReferenceBrokerSnapshotV2431(
        snapshot=snapshot,
        healthy=healthy,
        blockers=tuple(sorted(set(blockers))),
        diagnostics=diagnostics,
        artifact_path=str(artifact),
    )


def write_reference_snapshot_status_v2431(
    root: str | Path,
    result: ReferenceBrokerSnapshotV2431,
) -> Path:
    root = Path(root).resolve()
    path = root / "artifacts/production_runtime_v2_43_1/broker_snapshot_readonly.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "ibkr_reference_snapshot_v2_43_1",
        "status": "READY" if result.healthy else "BLOCKED",
        "healthy": result.healthy,
        "blockers": list(result.blockers),
        "diagnostics": result.diagnostics,
        "snapshot": result.snapshot.to_dict() if result.snapshot is not None else None,
        "source_artifact": result.artifact_path,
        "broker_write_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return path


__all__ = [
    "ReferenceBrokerSnapshotV2431",
    "fetch_reference_broker_snapshot_v2431",
    "write_reference_snapshot_status_v2431",
]
