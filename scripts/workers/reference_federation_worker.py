from __future__ import annotations

import json
import subprocess
from pathlib import Path

from _common import run_worker


ROLE_BY_INTEGRATION = {
    "lean_reference": "event_backtest_crosscheck",
    "optuna_reference": "train_validation_hyperparameter_search",
    "pybroker_reference": "walkforward_crosscheck",
    "skfolio_reference": "portfolio_risk_challenger",
    "sb3_contrib_reference": "experimental_rl_challenger",
    "vectorbt_reference": "fast_screen_only",
    "vnpy_ib_reference": "ibkr_shadow_reference",
}


def _git(repo: Path) -> dict:
    if not (repo / ".git").exists():
        return {"available": False}
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        remote = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        return {"available": True, "commit": commit, "origin": remote}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}:{exc}"}


def _catalog(repo: Path) -> dict:
    if not repo.exists():
        return {"files": 0, "python_files": 0, "top_level": []}
    files = [
        path
        for path in repo.rglob("*")
        if path.is_file() and ".git" not in path.parts
    ]
    top_level = sorted(
        path.name for path in repo.iterdir()
        if path.name != ".git"
    )[:80]
    return {
        "files": len(files),
        "python_files": sum(path.suffix == ".py" for path in files),
        "top_level": top_level,
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    del artifact_dir
    name = str(request["integration"])
    context = dict(request.get("context") or {})
    repo_raw = context.get("repo_path")
    repo = Path(repo_raw) if repo_raw else Path("__missing__")
    action = request["action"]

    role = ROLE_BY_INTEGRATION.get(name, "reference_engine")
    exists = repo.is_dir()
    common = {
        "repo": str(repo),
        "repo_exists": exists,
        "role": role,
        "money_control": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }

    if action == "health":
        return {
            "state": "OK" if exists else "DEGRADED",
            "data": {**common, "git": _git(repo) if exists else {"available": False}},
            "warnings": [] if exists else ["reference repository missing"],
        }

    if action == "catalog":
        return {
            "state": "OK" if exists else "DEGRADED",
            "data": {**common, "catalog": _catalog(repo)},
            "warnings": [] if exists else ["reference repository missing"],
        }

    if action == "role_manifest":
        return {
            "state": "OK" if exists else "DEGRADED",
            "data": {
                **common,
                "canonical_broker_writer": False,
                "automatic_live_promotion": False,
            },
            "warnings": [] if exists else ["reference repository missing"],
        }

    raise ValueError(f"unsupported reference federation action: {action}")


if __name__ == "__main__":
    run_worker(handle)
