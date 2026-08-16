#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

from stocks.integrations.reference_federation import (
    audit_reference_federation,
    load_reference_federation,
)
from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner

ROOT = Path(__file__).resolve().parents[1]


def _origin(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        return subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except Exception:
        return None


def _normalized_remote(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text.endswith(".git"):
        text = text[:-4]
    text = text.replace("git@github.com:", "https://github.com/")
    return text


def main() -> int:
    payload = load_reference_federation(ROOT)
    static_audit = audit_reference_federation(ROOT)

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    rows = []
    for engine, spec in payload["engines"].items():
        repo = ROOT / str(spec["local_repo"])
        configured = str(spec["upstream"])
        actual = _origin(repo)
        remote_match = (
            _normalized_remote(actual)
            == _normalized_remote(configured)
        )
        runtime = str(spec["runtime_integration"])
        runtime_registered = runtime in registry.names()

        health_state = "UNREGISTERED"
        health_error = None
        if runtime_registered:
            response = runner.health(runtime)
            health_state = response.state.value
            health_error = response.error

        rows.append(
            {
                "engine": engine,
                "repo": str(repo),
                "repo_exists": repo.is_dir(),
                "git_origin": actual,
                "expected_origin": configured,
                "remote_match": remote_match,
                "runtime_integration": runtime,
                "runtime_registered": runtime_registered,
                "runtime_health": health_state,
                "runtime_error": health_error,
                "roles": "|".join(spec.get("roles", [])),
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        )

    frame = pd.DataFrame(rows)
    output = (
        ROOT
        / "artifacts/research_runtime/"
        "reference_engine_federation_v2_16"
    )
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "engines.csv", index=False)

    all_present = bool(frame["repo_exists"].all())
    all_registered = bool(frame["runtime_registered"].all())
    remotes_ok = bool(frame["remote_match"].all())
    responsive = bool(
        frame["runtime_health"].isin(["OK", "DEGRADED"]).all()
    )
    audit = {
        "schema": "reference_engine_federation_audit_v2_16",
        **static_audit.to_dict(),
        "all_repositories_present": all_present,
        "all_runtime_integrations_registered": all_registered,
        "all_origin_remotes_match": remotes_ok,
        "all_runtimes_responsive": responsive,
        "healthy_or_degraded": int(
            frame["runtime_health"].isin(["OK", "DEGRADED"]).sum()
        ),
        "engines": int(len(frame)),
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    audit["ready"] = bool(
        static_audit.ok
        and all_present
        and all_registered
        and remotes_ok
        and responsive
    )

    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "REFERENCE_ENGINE_FEDERATION_V2_16",
        "ENGINES",
        len(frame),
        "PRESENT",
        int(frame["repo_exists"].sum()),
        "REGISTERED",
        int(frame["runtime_registered"].sum()),
        "REMOTE_MATCH",
        int(frame["remote_match"].sum()),
        "READY",
        audit["ready"],
    )
    print(
        frame[
            [
                "engine",
                "repo_exists",
                "remote_match",
                "runtime_integration",
                "runtime_health",
            ]
        ].to_string(index=False)
    )
    print("CANONICAL_BROKER_WRITER", audit["canonical_broker_writer"])
    print("WHOLE_SHARES_ONLY", audit["whole_shares_only"])
    print("FIXED_EURO_ORDER_CAP", audit["fixed_euro_order_cap"])
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0 if audit["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
