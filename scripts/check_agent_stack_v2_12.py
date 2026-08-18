#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata as metadata
import json
from pathlib import Path

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner


ROOT = Path(__file__).resolve().parents[1]


PACKAGES = {
    "gymnasium": "gymnasium",
    "stable-baselines3": "stable_baselines3",
    "sb3-contrib": "sb3_contrib",
    "pettingzoo": "pettingzoo",
    "transformers": "transformers",
    "torch": "torch",
}


def probe(distribution: str, module: str):
    try:
        imported = importlib.import_module(module)
        try:
            version = metadata.version(distribution)
        except Exception:
            version = getattr(imported, "__version__", None)
        return {
            "distribution": distribution,
            "module": module,
            "ok": True,
            "version": version,
        }
    except Exception as exc:
        return {
            "distribution": distribution,
            "module": module,
            "ok": False,
            "error": f"{type(exc).__name__}:{exc}",
        }


def main() -> int:
    local = [
        probe(distribution, module)
        for distribution, module in PACKAGES.items()
    ]

    registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(registry)

    integrations = {}
    for name in ("nautilus", "finrl", "qlib"):
        try:
            response = runner.health(name)
            integrations[name] = {
                "state": response.state.value,
                "ok": response.ok,
                "error": response.error,
                "warnings": list(response.warnings),
            }
        except Exception as exc:
            integrations[name] = {
                "state": "ERROR",
                "ok": False,
                "error": f"{type(exc).__name__}:{exc}",
            }

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_stack_v2_12"
    )
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent_stack_v2_12",
        "local_packages": local,
        "integrations": integrations,
        "execution_authority": "NONE",
    }
    (output / "health.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print("AGENT_STACK_V2_12")
    for row in local:
        print(
            "LOCAL",
            row["distribution"],
            "OK" if row["ok"] else "MISSING",
            row.get("version") or row.get("error"),
        )
    for name, row in integrations.items():
        print(
            "INTEGRATION",
            name,
            row["state"],
            "OK",
            row["ok"],
            "ERROR",
            row.get("error"),
        )

    missing_core = [
        row["distribution"]
        for row in local
        if not row["ok"]
        and row["distribution"]
        in {"gymnasium", "stable-baselines3", "sb3-contrib", "pettingzoo"}
    ]
    print("MISSING_CORE", "|".join(missing_core))
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
