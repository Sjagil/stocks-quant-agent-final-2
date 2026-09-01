#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.production.authority_v2_41 import (
    arm_live,
    authority_status,
    clear_kill_switch,
    configured_mode,
    disarm_live,
    engage_kill_switch,
    live_arm_status,
    set_mode,
    set_submission,
)
from stocks.production.data_refresh_v2_41_2 import refresh_provider_fabric
from stocks.production.ibkr_adapter_v2_41 import IBKRBrokerV241
from stocks.production.ibkr_read_facade_v2_43_1 import IBKRReadFacadeV2431
from stocks.production.launchd_v2_41 import LABEL, install_launchagent_v241, launchagent_path_v241, uninstall_launchagent_v241
from stocks.production.preflight_v2_41 import build_preflight
from stocks.production.proposal_adapter_v2_41 import eligible_buy_rows
from stocks.production.screener_v2_44 import run_production_screener_v244
from stocks.production.runtime_lock_v2_41 import exclusive_production_lock
from stocks.production.runtime_v2_41 import run_production_cycle_v241
from stocks.production.state_store_v2_41 import ProductionStoreV241


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def context(config: str | None = None):
    load_env(ROOT / ".env")
    path = Path(config) if config else ROOT / "config/production_runtime_v2_41.json"
    if not path.is_absolute():
        path = ROOT / path
    cfg = json.loads(path.read_text(encoding="utf-8"))
    store = ProductionStoreV241(ROOT / cfg["runtime"]["database"])
    return cfg, store


def preflight(cfg, store):
    with IBKRReadFacadeV2431(ROOT, cfg) as broker:
        snap = broker.snapshot()
        buys = eligible_buy_rows(ROOT, cfg)
        relevant = {str(x.get("symbol", "")).upper() for x in buys if x.get("symbol")}
        relevant |= store.managed_symbols()
        if not relevant:
            # Manual preflight is a production-universe readiness check, not a
            # no-op just because the current decision file has no buy candidate.
            relevant = {str(s).upper() for s in cfg["data"].get("symbols", [])}
        report = build_preflight(root=ROOT, cfg=cfg, store=store, snapshot=snap, relevant_symbols=relevant)
        return snap, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Production Runtime v2.41")
    parser.add_argument("--config", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    sub.add_parser("status")
    sub.add_parser("preflight")
    sub.add_parser("refresh-data")
    sub.add_parser("screener")
    cycle = sub.add_parser("cycle")
    cycle.add_argument("--force-data-refresh", action="store_true")
    cycle.add_argument("--force-decision-refresh", action="store_true")
    watch = sub.add_parser("watch")
    watch.add_argument("--interval-seconds", type=int, default=None)
    baseline = sub.add_parser("adopt-baseline")
    baseline.add_argument("--replace", action="store_true")
    mode = sub.add_parser("set-mode")
    mode.add_argument("mode", choices=["OBSERVE", "PAPER", "LIVE_CANARY"])
    enable = sub.add_parser("enable-submission")
    enable.add_argument("--environment", required=True, choices=["PAPER", "LIVE"])
    sub.add_parser("disable-submission")
    arm = sub.add_parser("arm-live")
    arm.add_argument("--hours", type=float, default=None)
    sub.add_parser("disarm-live")
    kill = sub.add_parser("kill")
    kill.add_argument("--reason", default="MANUAL_KILL_SWITCH")
    sub.add_parser("clear-kill")
    install = sub.add_parser("install-launchd")
    install.add_argument("--interval-seconds", type=int, default=300)
    sub.add_parser("uninstall-launchd")
    sub.add_parser("launchd-status")
    args = parser.parse_args()

    cfg, store = context(args.config)

    if args.cmd == "init":
        for key, path_key in (
            ("database", "database"),
            ("report", "report_path"),
            ("kill", "kill_switch_path"),
        ):
            (ROOT / cfg["runtime"][path_key]).parent.mkdir(parents=True, exist_ok=True)
        if store.get("submission_enabled", None) is None:
            set_submission(store, enabled=False)
        if store.get("execution_mode", None) is None:
            set_mode(store, cfg.get("mode", "PAPER"))
        print("PRODUCTION_V2_41_INIT_OK", ROOT / cfg["runtime"]["database"])
        print(json.dumps(authority_status(ROOT, cfg, store).to_dict(), indent=2))
        return 0

    if args.cmd == "doctor":
        checks = {
            "config": (ROOT / "config/production_runtime_v2_41.json").is_file(),
            "venv_python": (ROOT / ".venv/bin/python").is_file(),
            "eodhd_api_key_present": bool(os.environ.get("EODHD_API_KEY", "").strip()),
            "ibkr_environment_valid": os.environ.get(cfg["broker"]["environment_env"], "PAPER").upper() in {"PAPER", "LIVE"},
            "automatic_live_promotion_false": not cfg["authority"].get("automatic_live_promotion", False),
            "automatic_champion_promotion_false": not cfg["authority"].get("automatic_champion_promotion", False),
            "rl_direct_broker_control_false": not cfg["eligibility"].get("allow_rl_direct_broker_control", False),
            "current_session_provider_ibkr": cfg["data"].get("production_current_session_provider") == "IBKR",
            "finalized_history_isolated": bool(cfg["data"].get("finalized_history_root")),
            "all_symbol_freshness_required": cfg["data"].get("require_all_symbols_fresh") is True,
            "production_screener_config": (ROOT / "config/production_screener_v2_44.json").is_file(),
            "stocks_reference_repo": (ROOT / "references/Stocks/src/stocks").is_dir(),
            "stocks_reference_python": (ROOT / ".venvs/stocks/bin/python").is_file(),
        }
        try:
            import ib_async  # noqa: F401
            checks["ib_async"] = True
        except Exception:
            checks["ib_async"] = False
        checks["ready"] = all(checks.values())
        print(json.dumps(checks, indent=2))
        return 0 if checks["ready"] else 2

    if args.cmd == "status":
        screener_summary_path = ROOT / "artifacts/production_runtime_v2_44/screener/summary.json"
        payload = {
            "authority": authority_status(ROOT, cfg, store).to_dict(),
            "baseline_adopted": store.get("baseline_adopted", False),
            "baseline_positions": store.baseline(),
            "expected_positions": store.expected_positions(),
            "managed_symbols": sorted(store.managed_symbols()),
            "recent_intents": store.recent_intents(),
            "recent_cycles": store.latest_cycles(),
            "production_screener": (
                json.loads(screener_summary_path.read_text(encoding="utf-8"))
                if screener_summary_path.is_file()
                else {"status": "MISSING", "fresh": False}
            ),
        }
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.cmd == "refresh-data":
        result = refresh_provider_fabric(ROOT, cfg)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("status") == "SUCCEEDED" else 2

    if args.cmd == "screener":
        frame, result, output = run_production_screener_v244(ROOT)
        print(json.dumps(result.to_dict(), indent=2, default=str))
        print("CANDIDATES", len(frame))
        print("OUTPUT", output)
        return 0 if result.status == "SUCCEEDED" else 2

    if args.cmd == "preflight":
        snap, report = preflight(cfg, store)
        print(json.dumps({"snapshot": snap.to_dict(), "preflight": report.to_dict()}, indent=2, default=str))
        return 0 if report.passed else 3

    if args.cmd == "cycle":
        result = run_production_cycle_v241(
            ROOT, cfg,
            force_data_refresh=args.force_data_refresh,
            force_decision_refresh=args.force_decision_refresh,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("status") in {"SUCCEEDED", "DEGRADED"} else 2

    if args.cmd == "adopt-baseline":
        if store.get("baseline_adopted", False) and not args.replace:
            raise SystemExit("baseline already adopted; use --replace only after verifying the broker account state")
        with IBKRBrokerV241(cfg, readonly=True) as broker:
            snap = broker.snapshot()
        if snap.open_orders:
            raise SystemExit("BASELINE_ADOPTION_BLOCKED: broker has open orders")
        shorts = {s: q for s, q in snap.positions.items() if float(q) < 0}
        if shorts:
            raise SystemExit(f"BASELINE_ADOPTION_BLOCKED: long-only runtime cannot adopt short positions: {shorts}")
        store.adopt_baseline(snap.positions)
        print("BASELINE_ADOPTED", json.dumps(store.baseline(), sort_keys=True))
        print("BROKER_WRITE_CALLS", snap.broker_write_calls)
        return 0

    if args.cmd == "set-mode":
        parsed = set_mode(store, args.mode)
        set_submission(store, enabled=False)
        print("MODE", parsed.value)
        print("SUBMISSION_ENABLED False")
        return 0

    if args.cmd == "enable-submission":
        mode = configured_mode(store, cfg)
        env = args.environment.upper()
        if mode.value == "OBSERVE":
            raise SystemExit("cannot enable submission in OBSERVE mode")
        if mode.value == "PAPER" and env != "PAPER":
            raise SystemExit("PAPER mode requires PAPER submission environment")
        if mode.value == "LIVE_CANARY":
            if env != "LIVE":
                raise SystemExit("LIVE_CANARY mode requires LIVE environment")
            armed, until = live_arm_status(ROOT, cfg)
            if not armed:
                raise SystemExit("LIVE_CANARY submission requires active arm-live state")
            if float(cfg["risk"].get("max_live_canary_notional_eur", 0) or 0) <= 0:
                raise SystemExit("LIVE_CANARY disabled: max_live_canary_notional_eur must be configured > 0")
        set_submission(store, enabled=True, environment=env)
        print("SUBMISSION_ENABLED True")
        print("SUBMISSION_ENVIRONMENT", env)
        return 0

    if args.cmd == "disable-submission":
        set_submission(store, enabled=False)
        print("SUBMISSION_ENABLED False")
        return 0

    if args.cmd == "arm-live":
        if configured_mode(store, cfg).value != "LIVE_CANARY":
            raise SystemExit("set-mode LIVE_CANARY before arm-live")
        payload = arm_live(ROOT, cfg, hours=args.hours)
        print(json.dumps(payload, indent=2))
        return 0

    if args.cmd == "disarm-live":
        disarm_live(ROOT, cfg)
        set_submission(store, enabled=False)
        print("LIVE_DISARMED True")
        print("SUBMISSION_ENABLED False")
        return 0

    if args.cmd == "kill":
        path = engage_kill_switch(ROOT, cfg, args.reason)
        set_submission(store, enabled=False)
        print("KILL_SWITCH", path)
        print("SUBMISSION_ENABLED False")
        return 0

    if args.cmd == "clear-kill":
        clear_kill_switch(ROOT, cfg)
        set_submission(store, enabled=False)
        print("KILL_SWITCH_CLEAR True")
        print("SUBMISSION_ENABLED False")
        return 0

    if args.cmd == "watch":
        interval = int(args.interval_seconds or cfg["runtime"].get("cycle_seconds", 300))
        if interval < 60:
            raise SystemExit("interval must be >=60 seconds")
        with exclusive_production_lock(ROOT / cfg["runtime"]["lock_path"]):
            print("PRODUCTION_V2_41_RUNNING", "interval", interval, flush=True)
            print("AUTOMATIC_LIVE_PROMOTION False", flush=True)
            print("RL_DIRECT_BROKER_CONTROL False", flush=True)
            while True:
                try:
                    result = run_production_cycle_v241(ROOT, cfg)
                    print(json.dumps({
                        "cycle_id": result.get("cycle_id"),
                        "status": result.get("status"),
                        "mode": result.get("mode"),
                        "planned": len(result.get("planned", [])),
                        "submitted": len(result.get("submitted", [])),
                        "errors": len(result.get("errors", [])),
                        "broker_write_calls": result.get("broker_write_calls", 0),
                    }, sort_keys=True), flush=True)
                except Exception as exc:
                    print("PRODUCTION_CYCLE_FAILED", type(exc).__name__, exc, file=sys.stderr, flush=True)
                time.sleep(interval)

    if args.cmd == "install-launchd":
        plist = install_launchagent_v241(ROOT, interval_seconds=args.interval_seconds)
        uid = os.getuid()
        subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(plist)], check=False, capture_output=True)
        proc = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist)], check=False, capture_output=True, text=True)
        print("LAUNCHAGENT", plist)
        print("LABEL", LABEL)
        print("BOOTSTRAP_RETURNCODE", proc.returncode)
        if proc.stderr.strip():
            print("BOOTSTRAP_STDERR", proc.stderr.strip())
        return proc.returncode

    if args.cmd == "uninstall-launchd":
        plist = launchagent_path_v241()
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)], check=False, capture_output=True)
        uninstall_launchagent_v241()
        print("REMOVED", plist)
        return 0

    if args.cmd == "launchd-status":
        proc = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"], check=False, capture_output=True, text=True)
        print(proc.stdout if proc.returncode == 0 else proc.stderr)
        return proc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
