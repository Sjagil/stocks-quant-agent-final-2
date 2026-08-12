from __future__ import annotations

import pkgutil
from pathlib import Path

from _common import base_health, import_probe, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog")


def handle(request: dict, artifact_dir: Path) -> dict:
    del artifact_dir
    repo = (request.get("context") or {}).get("repo_path")
    action = request["action"]
    if action == "health":
        return base_health(
            request,
            distributions=("nautilus_trader",),
            imports=("nautilus_trader",),
            capabilities=CAPABILITIES,
        )
    if action == "catalog":
        probe = import_probe("nautilus_trader")
        modules: list[str] = []
        warnings: list[str] = []
        state = "OK"
        if probe["ok"]:
            import nautilus_trader

            modules = sorted(module.name for module in pkgutil.iter_modules(nautilus_trader.__path__))
        else:
            state = "DEGRADED"
            warnings.append(
                "NautilusTrader runtime package is unavailable; reference-repository catalog is still reported"
            )
        return {
            "state": state,
            "data": {
                "runtime": probe,
                "top_level_modules": modules,
                "repo_catalog": repo_catalog(repo, ("*fill*.py", "*execution*.py", "*backtest*.py", "*risk*.py")),
                "purpose": "Independent event/execution simulation challenger for finalists; no live authority.",
            },
            "warnings": warnings,
        }
    raise ValueError(f"unsupported nautilus action: {action}")


if __name__ == "__main__":
    run_worker(handle)
