from __future__ import annotations

from pathlib import Path

from _common import add_repo_src, base_health, import_probe, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog")


def handle(request: dict, artifact_dir: Path) -> dict:
    del artifact_dir
    repo = (request.get("context") or {}).get("repo_path")
    add_repo_src(repo)
    action = request["action"]
    if action == "health":
        core_imports = (
            "numpy",
            "pandas",
            "sklearn",
            "scipy",
            "lightgbm",
            "xgboost",
            "torch",
            "pandas_market_calendars",
        )
        result = base_health(request, distributions=(), imports=core_imports, capabilities=CAPABILITIES)
        repo_ok = bool(repo and Path(repo).exists())
        optional = [import_probe("finnhub")]
        result["data"]["optional_imports"] = optional
        result["data"]["repo_import_path_added"] = str(Path(repo) / "src") if repo else None
        warnings = list(result.get("warnings") or [])
        warnings.extend(
            f"Optional FinRL dependency unavailable: {item['error']}"
            for item in optional
            if not item["ok"]
        )
        if not repo_ok:
            warnings.append("FinRL repository is missing")
            result["state"] = "DEGRADED"
        result["warnings"] = warnings
        return result
    if action == "catalog":
        return {
            "state": "OK",
            "data": {
                "repo_catalog": repo_catalog(
                    repo,
                    ("*walk_forward*.py", "*risk*.py", "*portfolio*.py", "*rotation*.py", "*rl*.py"),
                ),
                "purpose": "Weight-centric multi-asset/rotation RL challenger; no direct trading authority.",
            },
        }
    raise ValueError(f"unsupported finrl action: {action}")


if __name__ == "__main__":
    run_worker(handle)
