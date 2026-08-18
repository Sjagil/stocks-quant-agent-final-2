#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from stocks.orchestration.forward_signal_engine_v2_19 import (
    write_validated_forward_signal_state,
)
from stocks.orchestration.validated_strategy_deployment_v2_19 import (
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT_ROOT,
    exclusive_run_lock,
    verify_validated_strategy_deployment,
    write_validated_strategy_deployment,
)

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = DEFAULT_OUTPUT_ROOT / "last_run.json"


def _run(label: str, command: list[str]) -> None:
    print("=" * 100)
    print("RUN", label)
    print("COMMAND", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    print("RESULT", label, completed.returncode)
    if completed.returncode != 0:
        raise RuntimeError(f"{label}_FAILED:{completed.returncode}")


def _atomic_state(payload: dict) -> None:
    path = ROOT / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-v2-18", action="store_true")
    parser.add_argument("--limit-symbols", type=int, default=5)
    parser.add_argument("--skip-forward-signals", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))
    timeout = int(config["automation"]["lock_timeout_seconds"])
    lock_path = ROOT / DEFAULT_OUTPUT_ROOT / ".automation.lock"

    with exclusive_run_lock(lock_path, timeout_seconds=timeout):
        try:
            if args.refresh_v2_18:
                _run(
                    "REFRESH_V2_18_HANDOFF",
                    [
                        sys.executable,
                        "scripts/run_cross_engine_finalization_v2_18.py",
                        "--refresh-v2-17",
                        "--limit-symbols",
                        str(args.limit_symbols),
                    ],
                )

            registry, _, audit, destination, changed = (
                write_validated_strategy_deployment(ROOT)
            )
            verification = verify_validated_strategy_deployment(ROOT)
            if not verification["valid"]:
                raise RuntimeError(
                    "DEPLOYMENT_AUDIT_FAILED:" + "|".join(verification["errors"])
                )

            signal_rows = 0
            new_entries = 0
            if not args.skip_forward_signals:
                signals, signal_audit, _ = write_validated_forward_signal_state(ROOT)
                signal_rows = len(signals)
                new_entries = int(signal_audit.get("new_entry_ready", 0))

            state = {
                "schema": "validated_strategy_automation_run_v2_19",
                "status": "READY",
                "output_changed": changed,
                "eligible_strategies": len(registry),
                "signal_rows": signal_rows,
                "new_entry_ready": new_entries,
                "registry_sha256": audit["registry_sha256"],
                "source_fingerprint": audit["source_fingerprint"],
                "automatic_live_promotion": False,
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
            _atomic_state(state)
        except Exception as exc:
            _atomic_state(
                {
                    "schema": "validated_strategy_automation_run_v2_19",
                    "status": "BLOCKED",
                    "error": f"{type(exc).__name__}:{exc}",
                    "automatic_live_promotion": False,
                    "broker_calls": 0,
                    "order_calls": 0,
                    "execution_authority": "NONE",
                }
            )
            raise

    print("=" * 100)
    print("VALIDATED_STRATEGY_AUTOMATION_V2_19", state["status"])
    print("ELIGIBLE_STRATEGIES", state["eligible_strategies"])
    print("OUTPUT_CHANGED", state["output_changed"])
    print("SIGNAL_ROWS", state["signal_rows"])
    print("NEW_ENTRY_READY", state["new_entry_ready"])
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT_ROOT", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
