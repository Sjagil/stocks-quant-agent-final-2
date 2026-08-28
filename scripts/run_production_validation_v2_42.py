#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"


def run(args):
    p = subprocess.run(
        [str(PYTHON), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": args,
        "returncode": p.returncode,
        "stdout_tail": p.stdout[-12000:],
        "stderr_tail": p.stderr[-6000:],
    }


if __name__ == "__main__":
    checks = {
        "finbert": run(["scripts/warm_finbert_v2_42.py"]),
        "strategy_hydration": run(["scripts/run_strategy_candidate_hydration_v2_42.py"]),
        "market_context_snapshot": run(["scripts/run_market_context_snapshot_v2_43.py"]),
        "forward_signals": run(["scripts/run_forward_signal_engine.py"]),
        "portfolio": run(["scripts/run_portfolio_decision_v2.py"]),
        "intelligence": run(["scripts/run_production_intelligence_v2_42.py"]),
        "agent_shadow": run(["scripts/run_agent_shadow_advisory_v2_42.py"]),
        "mappo_dataset": run(["scripts/build_mappo_dataset_v2_42.py"]),
        "context_walk_forward": run(["scripts/run_context_walk_forward_v2_43.py"]),
        "context_readiness": run(["scripts/run_context_validation_v2_43.py"]),
        "production_preflight": run(["scripts/run_production_runtime_v2_41.py", "preflight"]),
    }
    implementation_keys = {
        "finbert", "strategy_hydration", "market_context_snapshot",
        "forward_signals", "portfolio", "intelligence", "agent_shadow",
        "mappo_dataset", "context_walk_forward", "context_readiness",
    }
    passed = all(checks[key]["returncode"] == 0 for key in implementation_keys)
    readiness_path = ROOT / "artifacts/production_runtime_v2_43/context_readiness.json"
    readiness = (
        json.loads(readiness_path.read_text(encoding="utf-8"))
        if readiness_path.is_file()
        else {"status": "MISSING", "paper_entry_ready": False}
    )
    result = {
        "schema": "production_validation_v2_43",
        "checks": checks,
        "pipeline_implementation_ready": passed,
        "paper_context_readiness": readiness,
        "order_submission_performed": False,
        "execution_authority": "NONE",
    }
    out = ROOT / "artifacts/production_runtime_v2_43/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("ORDER_SUBMISSION_PERFORMED False")
    raise SystemExit(0 if passed else 2)
