#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(name: str, command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--skip-context", action="store_true")
    parser.add_argument("--skip-indicators", action="store_true")
    parser.add_argument("--skip-generated-strategies", action="store_true")
    args = parser.parse_args()

    jobs: list[tuple[str, list[str]]] = []
    if not args.skip_context:
        command = [sys.executable, "scripts/run_contextual_discovery.py", "--limit", str(args.limit)]
        if args.as_of:
            command += ["--as-of", args.as_of]
        jobs.append(("contextual_discovery", command))
    if not args.skip_indicators:
        jobs.append(("indicator_discovery", [sys.executable, "scripts/run_indicator_strategy_discovery.py"]))
    if not args.skip_generated_strategies:
        jobs.append((
            "strategy_generation_v2_22",
            [sys.executable, "scripts/run_strategy_generation_v2_22.py"],
        ))

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as executor:
        futures = [executor.submit(_run, name, command) for name, command in jobs]
        results = [future.result() for future in futures]

    for result in results:
        print("=" * 78)
        print(result["name"], "OK" if result["ok"] else "FAILED", "RC", result["returncode"])
        if result["stdout"]:
            print(result["stdout"].rstrip())
        if result["stderr"]:
            print("STDERR")
            print(result["stderr"].rstrip())

    registry = _run("research_candidate_registry", [sys.executable, "scripts/build_research_candidate_registry.py"])
    print("=" * 78)
    print(registry["name"], "OK" if registry["ok"] else "FAILED", "RC", registry["returncode"])
    if registry["stdout"]:
        print(registry["stdout"].rstrip())
    if registry["stderr"]:
        print("STDERR")
        print(registry["stderr"].rstrip())

    audit_root = ROOT / "artifacts/research_runtime/parallel_research"
    audit_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "parallel_research_run_v1",
        "lanes": [{key: value for key, value in item.items() if key not in {"stdout", "stderr"}} for item in results],
        "registry": {key: value for key, value in registry.items() if key not in {"stdout", "stderr"}},
        "context_failure_does_not_block_indicator_research": True,
        "indicator_failure_does_not_escalate_authority": True,
        "generated_strategy_failure_does_not_escalate_authority": True,
        "execution_authority": "NONE",
    }
    (audit_root / "audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if registry["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
