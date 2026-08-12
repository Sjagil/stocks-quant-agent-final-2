from __future__ import annotations

import pkgutil
from pathlib import Path

from _common import base_health, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog")


def handle(request: dict, artifact_dir: Path) -> dict:
    del artifact_dir
    repo = (request.get("context") or {}).get("repo_path")
    action = request["action"]
    if action == "health":
        return base_health(request, distributions=("pyqlib",), imports=("qlib",), capabilities=CAPABILITIES)
    if action == "catalog":
        import qlib
        modules = sorted(module.name for module in pkgutil.iter_modules(qlib.__path__))
        return {
            "state": "OK",
            "data": {
                "top_level_modules": modules,
                "repo_catalog": repo_catalog(repo, ("workflow_config_*Alpha158*.yaml", "workflow_config_*Alpha360*.yaml", "*model*.py", "*risk*.py")),
                "purpose": "Independent ML experiment/model/risk-model challenger. Training remains a later explicit pipeline stage.",
            },
        }
    raise ValueError(f"unsupported qlib action: {action}")


if __name__ == "__main__":
    run_worker(handle)
