#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"

def run(args):
    p = subprocess.run([str(PYTHON), *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return {"args": args, "returncode": p.returncode, "stdout_tail": p.stdout[-12000:], "stderr_tail": p.stderr[-6000:]}

if __name__ == "__main__":
    checks = {
        "finbert": run(["scripts/warm_finbert_v2_42.py"]),
        "strategy_hydration": run(["scripts/run_strategy_candidate_hydration_v2_42.py"]),
        "forward_signals": run(["scripts/run_forward_signal_engine.py"]),
        "portfolio": run(["scripts/run_portfolio_decision_v2.py"]),
        "intelligence": run(["scripts/run_production_intelligence_v2_42.py"]),
        "agent_shadow": run(["scripts/run_agent_shadow_advisory_v2_42.py"]),
        "mappo_dataset": run(["scripts/build_mappo_dataset_v2_42.py"]),
        "production_preflight": run(["scripts/run_production_runtime_v2_41.py", "preflight"]),
    }
    passed = all(v["returncode"] == 0 for k, v in checks.items() if k != "production_preflight")
    payload = {"schema": "production_validation_v2_42", "checks": checks, "pipeline_inputs_ready": passed, "order_submission_performed": False, "execution_authority": "NONE"}
    out = ROOT / "artifacts/production_runtime_v2_42/validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    print("ORDER_SUBMISSION_PERFORMED False")
    raise SystemExit(0 if passed else 2)
