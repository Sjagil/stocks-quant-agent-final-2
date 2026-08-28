#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.learning.config_v2_40 import agent_specs_v240, load_learning_config_v240, resolve_runtime_paths_v240
from stocks.learning.launchd_v2_40 import LABEL, install_launchagent_v240, launchagent_path_v240, uninstall_launchagent_v240
from stocks.learning.learning_cycle_v2_40 import run_learning_cycle_v240
from stocks.learning.runtime_lock_v2_40 import exclusive_learning_lock_v240
from stocks.learning.state_store_v2_40 import LearningStoreV240


def context(args):
    cfg = load_learning_config_v240(ROOT, args.config)
    paths = resolve_runtime_paths_v240(ROOT, cfg)
    store = LearningStoreV240(paths["database"])
    for spec in agent_specs_v240(cfg):
        store.upsert_agent(spec)
    return cfg, paths, store


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous Continuous Learning Runtime v2.40")
    parser.add_argument("--config", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("agents")
    cycle = sub.add_parser("cycle")
    cycle.add_argument("--force-train", action="store_true")
    cycle.add_argument("--force-strategy-refresh", action="store_true")
    watch = sub.add_parser("watch")
    watch.add_argument("--interval-seconds", type=int, default=None)
    train = sub.add_parser("train-agent")
    train.add_argument("--agent-id", required=True)
    sub.add_parser("doctor")
    install = sub.add_parser("install-launchd")
    install.add_argument("--interval-seconds", type=int, default=900)
    sub.add_parser("uninstall-launchd")
    sub.add_parser("launchd-status")
    args = parser.parse_args()

    cfg, paths, store = context(args)
    if args.cmd == "init":
        for p in (paths["runtime_root"], paths["models"], paths["reports"]):
            p.mkdir(parents=True, exist_ok=True)
        print("AUTONOMOUS_LEARNING_V2_40_INIT_OK", store.path)
        print("EXECUTION_AUTHORITY NONE")
        return 0
    if args.cmd == "status":
        print(json.dumps(store.status(), indent=2, default=str))
        return 0
    if args.cmd == "agents":
        print(json.dumps(store.agents(), indent=2, default=str))
        return 0
    if args.cmd == "cycle":
        result = run_learning_cycle_v240(ROOT, cfg, force_train=args.force_train, force_strategy_refresh=args.force_strategy_refresh)
        print(json.dumps(result, indent=2, default=str))
        return 0
    if args.cmd == "train-agent":
        # A one-agent forced cycle uses the same safety/research path. Temporarily disable others in memory.
        wanted = args.agent_id
        rows = [row for row in cfg.get("agents", []) if row.get("agent_id") == wanted]
        if not rows:
            raise SystemExit(f"unknown agent: {wanted}")
        cfg = dict(cfg)
        cfg["agents"] = rows
        result = run_learning_cycle_v240(ROOT, cfg, force_train=True)
        print(json.dumps(result, indent=2, default=str))
        return 0
    if args.cmd == "doctor":
        scripts = cfg.get("strategy_runtime") or {}
        checks = {
            "venv_python": (ROOT / ".venv/bin/python").is_file(),
            "rl_config": (ROOT / "config/rl.yaml").is_file(),
            "continuous_research": (ROOT / scripts.get("continuous_research_script", "")).is_file(),
            "evidence_producer": (ROOT / scripts.get("evidence_production_script", "")).is_file(),
            "parallel_research": (ROOT / scripts.get("parallel_research_script", "")).is_file(),
            "shadow_lifecycle": (ROOT / scripts.get("shadow_lifecycle_script", "")).is_file(),
            "execution_authority_none": cfg.get("execution_authority") == "NONE",
            "broker_submission_false": not cfg.get("broker_submission_enabled"),
            "automatic_live_promotion_false": not cfg.get("automatic_live_promotion"),
            "automatic_champion_promotion_false": not cfg.get("automatic_champion_promotion"),
        }
        for spec in agent_specs_v240(cfg):
            p = Path(spec.data_path)
            if not p.is_absolute():
                p = ROOT / p
            checks[f"data_{spec.agent_id}"] = p.is_file()
        try:
            import stable_baselines3  # noqa: F401
            checks["stable_baselines3"] = True
        except Exception:
            checks["stable_baselines3"] = False
        try:
            import torch  # noqa: F401
            checks["torch"] = True
        except Exception:
            checks["torch"] = False
        checks["ready_for_configured_sb3_agents"] = all(v for k, v in checks.items() if k != "torch")
        print(json.dumps(checks, indent=2))
        return 0 if checks["ready_for_configured_sb3_agents"] else 2
    if args.cmd == "watch":
        interval = int(args.interval_seconds or cfg.get("runtime", {}).get("cycle_seconds", 900))
        minimum = int(cfg.get("runtime", {}).get("minimum_cycle_seconds", 60))
        if interval < minimum:
            raise SystemExit(f"interval must be >= {minimum} seconds")
        with exclusive_learning_lock_v240(paths["lock"]):
            print("AUTONOMOUS_LEARNING_V2_40_RUNNING", "interval", interval)
            print("EVENT_DRIVEN_RETRAINING True")
            print("EXECUTION_AUTHORITY NONE")
            while True:
                try:
                    result = run_learning_cycle_v240(ROOT, cfg)
                    print(json.dumps({"cycle_id": result.get("cycle_id"), "trained": len(result.get("trained", [])), "errors": len(result.get("errors", []))}, sort_keys=True), flush=True)
                except Exception as exc:
                    print("LEARNING_CYCLE_FAILED", type(exc).__name__, exc, file=sys.stderr, flush=True)
                time.sleep(interval)
    if args.cmd == "install-launchd":
        plist = install_launchagent_v240(ROOT, interval_seconds=args.interval_seconds)
        subprocess.run(["launchctl", "bootout", f"gui/{__import__('os').getuid()}", str(plist)], check=False, capture_output=True)
        proc = subprocess.run(["launchctl", "bootstrap", f"gui/{__import__('os').getuid()}", str(plist)], check=False, text=True, capture_output=True)
        print("LAUNCHAGENT", plist)
        print("LABEL", LABEL)
        print("BOOTSTRAP_RETURNCODE", proc.returncode)
        if proc.stderr.strip():
            print("BOOTSTRAP_STDERR", proc.stderr.strip())
        print("EXECUTION_AUTHORITY NONE")
        return 0 if proc.returncode == 0 else proc.returncode
    if args.cmd == "uninstall-launchd":
        plist = launchagent_path_v240()
        subprocess.run(["launchctl", "bootout", f"gui/{__import__('os').getuid()}", str(plist)], check=False, capture_output=True)
        uninstall_launchagent_v240()
        print("REMOVED", plist)
        return 0
    if args.cmd == "launchd-status":
        proc = subprocess.run(["launchctl", "print", f"gui/{__import__('os').getuid()}/{LABEL}"], check=False, text=True, capture_output=True)
        print(proc.stdout if proc.returncode == 0 else proc.stderr)
        return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
