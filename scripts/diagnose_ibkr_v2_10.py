#!/usr/bin/env python3
from __future__ import annotations
import json, os
from pathlib import Path
from stocks.orchestration.runtime_unblock_v2_10 import choose_open_port, probe_tcp
from stocks.providers.env import load_project_env

ROOT = Path(__file__).resolve().parents[1]

def _integer(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None

def main() -> int:
    load_project_env(ROOT)
    host = os.environ.get("IBKR_HOST", "127.0.0.1").strip()
    configured_port = _integer("IBKR_PORT")
    primary = _integer("IBKR_CLIENT_ID")
    recon = _integer("IBKR_RECON_CLIENT_ID")
    base = os.environ.get("IBKR_ACCOUNT_BASE_CURRENCY", "").strip().upper()
    print("IBKR_DIAGNOSTIC_V2_10", "HOST", host, "CONFIGURED_PORT", configured_port,
          "PRIMARY_ID_NONZERO", bool(primary), "RECON_ID_NONZERO", bool(recon),
          "IDS_DISTINCT", bool(primary and recon and primary != recon),
          "BASE_CURRENCY", base or "MISSING")
    if configured_port is None:
        print("BLOCKER IBKR_PORT_INVALID_OR_MISSING")
        return 2
    ports = list(dict.fromkeys((configured_port, 7497, 7496)))
    results = {}
    for port in ports:
        result = probe_tcp(host, port)
        results[port] = bool(result["open"])
        print("TCP_PROBE", f"{host}:{port}", "OPEN" if result["open"] else "CLOSED")
    selected = choose_open_port(configured_port, results)
    if selected is None:
        print("IBKR_SOCKET_READY", False)
        print("NEXT_ACTION", "START_TWS_OR_IB_GATEWAY_AND_ENABLE_API_SOCKET")
    elif selected != configured_port:
        print("IBKR_SOCKET_READY", True)
        print("CONFIGURED_PORT_MISMATCH", f"IBKR_PORT={configured_port}", "LISTENING_PORT", selected)
        print("NEXT_ACTION", f"SET_IBKR_PORT_{selected}")
    else:
        print("IBKR_SOCKET_READY", True)
        print("CONFIGURED_PORT_LISTENING", configured_port)
    snap = ROOT / "artifacts/research_runtime/ibkr_readonly_v2_9/snapshot.json"
    if snap.is_file():
        try:
            payload = json.loads(snap.read_text(encoding="utf-8"))
            economic = payload.get("economic_account_state") or {}
            snapshot = payload.get("snapshot") or {}
            print("LAST_SNAPSHOT", "LIFECYCLE", economic.get("lifecycle_state"),
                  "STABLE", payload.get("double_snapshot_stable"),
                  "SERVER_VERSION_PRESENT", bool(snapshot.get("server_version")),
                  "BROKER_WRITES", payload.get("broker_write_calls", 0))
            print("LAST_EXECUTION_BLOCKERS", "|".join(economic.get("execution_blockers") or []))
        except Exception as exc:
            print("LAST_SNAPSHOT", "INVALID", type(exc).__name__)
    if not base:
        print("CONFIG_NOTE", "SET_IBKR_ACCOUNT_BASE_CURRENCY=EUR_EXPLICITLY")
    if not primary or not recon or primary == recon:
        print("BLOCKER", "IBKR_CLIENT_ID_CONFIGURATION_INVALID")
        return 2
    return 0 if selected is not None else 2

if __name__ == "__main__":
    raise SystemExit(main())
