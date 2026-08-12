from __future__ import annotations

import sys
from pathlib import Path

from _common import add_repo_src, base_health, import_probe, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog")


def install_pandas_ta_compat() -> dict:
    direct = import_probe("pandas_ta")
    if direct["ok"]:
        return {"backend": "pandas_ta", "ok": True, "probe": direct, "compat_alias": False}

    classic = import_probe("pandas_ta_classic")
    if classic["ok"]:
        import pandas_ta_classic as pandas_ta_classic

        sys.modules.setdefault("pandas_ta", pandas_ta_classic)
        return {
            "backend": "pandas_ta_classic",
            "ok": True,
            "probe": classic,
            "compat_alias": True,
            "note": "pandas_ta is aliased in-process to pandas_ta_classic; upstream MoonDev files remain untouched",
        }

    return {
        "backend": None,
        "ok": False,
        "probe": direct,
        "fallback_probe": classic,
        "compat_alias": False,
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    del artifact_dir
    repo = (request.get("context") or {}).get("repo_path")
    add_repo_src(repo)
    ta_compat = install_pandas_ta_compat()
    action = request["action"]
    if action == "health":
        result = base_health(
            request,
            distributions=(),
            imports=("pandas", "numpy", "requests", "fastapi", "openai"),
            capabilities=CAPABILITIES,
        )
        result["data"]["technical_analysis"] = ta_compat
        warnings = list(result.get("warnings") or [])
        if not ta_compat["ok"]:
            warnings.append(
                "Optional MoonDev technical-analysis helpers are unavailable: install pandas-ta-classic in .venvs/moondev"
            )
        if not repo or not Path(repo).exists():
            result["state"] = "DEGRADED"
            warnings.append("MoonDev repository is missing")
        result["warnings"] = warnings
        return result
    if action == "catalog":
        return {
            "state": "OK",
            "data": {
                "repo_catalog": repo_catalog(repo, ("*_agent.py", "*_BT*.py", "*strategy*.txt")),
                "purpose": "Hypothesis/RBI/risk-critic research reference only. Trading agents are never invoked by this worker.",
                "technical_analysis": ta_compat,
                "safety": {"trading_agent_execution": False, "broker_execution": False},
            },
        }
    raise ValueError(f"unsupported moondev action: {action}")


if __name__ == "__main__":
    run_worker(handle)
