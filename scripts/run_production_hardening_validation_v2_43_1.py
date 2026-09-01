#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"


def run(args: list[str]) -> dict:
    proc = subprocess.run(
        [str(PYTHON), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": args,
        "returncode": int(proc.returncode),
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-8000:],
    }


def main() -> int:
    checks: dict[str, dict] = {}
    checks["finbert"] = run(["scripts/warm_finbert_v2_42.py"])
    checks["ibkr_reference_snapshot"] = run(["scripts/run_ibkr_reference_snapshot_v2_43_1.py"])
    checks["reference_macro"] = run(["scripts/run_reference_macro_v2_43_1.py"])
    checks["strategy_hydration"] = run(["scripts/run_strategy_candidate_hydration_v2_42.py"])
    checks["market_context_snapshot"] = run(["scripts/run_market_context_snapshot_v2_43.py"])

    # Causal decision chain is fail-fast after hydration. Diagnostic context and
    # broker checks above are still allowed to run so failures are actionable.
    if checks["strategy_hydration"]["returncode"] == 0:
        checks["forward_signals"] = run(["scripts/run_forward_signal_engine.py"])
        if checks["forward_signals"]["returncode"] == 0:
            checks["portfolio"] = run(["scripts/run_portfolio_decision_v2.py"])
            if checks["portfolio"]["returncode"] == 0:
                checks["intelligence"] = run(["scripts/run_production_intelligence_v2_42.py"])

    checks["agent_shadow"] = run(["scripts/run_agent_shadow_advisory_v2_42.py"])
    checks["mappo_dataset"] = run(["scripts/build_mappo_dataset_v2_42.py"])
    checks["historical_context_replay"] = run(["scripts/run_context_historical_replay_v2_43_1.py"])
    checks["context_walk_forward"] = run(["scripts/run_context_walk_forward_v2_43.py"])
    checks["context_readiness"] = run(["scripts/run_context_validation_v2_43.py"])

    readiness_path = ROOT / "artifacts/production_runtime_v2_43/context_readiness.json"
    readiness = (
        json.loads(readiness_path.read_text(encoding="utf-8"))
        if readiness_path.is_file()
        else {"status": "MISSING", "system_paper_ready": False, "entry_eligible_now": False}
    )
    mandatory = [
        "finbert", "ibkr_reference_snapshot", "strategy_hydration",
        "market_context_snapshot", "agent_shadow", "mappo_dataset",
        "context_walk_forward", "context_readiness",
    ]
    implementation_ready = all(
        checks.get(key, {}).get("returncode") == 0 for key in mandatory
    ) and all(
        checks.get(key, {}).get("returncode") == 0
        for key in ("forward_signals", "portfolio", "intelligence")
    )
    result = {
        "schema": "production_hardening_validation_v2_43_1",
        "checks": checks,
        "pipeline_implementation_ready": implementation_ready,
        "system_paper_ready": bool(readiness.get("system_paper_ready", False)),
        "entry_eligible_now": bool(readiness.get("entry_eligible_now", False)),
        "paper_entry_ready": bool(readiness.get("paper_entry_ready", False)),
        "paper_context_readiness": readiness,
        "order_submission_performed": False,
        "broker_submission_enabled": False,
        "rl_direct_broker_control": False,
        "execution_authority": "NONE",
    }
    out = ROOT / "artifacts/production_runtime_v2_43_1/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("ORDER_SUBMISSION_PERFORMED False")
    return 0 if implementation_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
