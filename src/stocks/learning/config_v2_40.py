from __future__ import annotations

import json
from pathlib import Path

from .contracts_v2_40 import AgentSpecV240


DEFAULT_CONFIG = Path("config/autonomous_continuous_learning_v2_40.json")


def load_learning_config_v240(project_root: str | Path, path: str | Path | None = None) -> dict:
    root = Path(project_root).resolve()
    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = root / config_path
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "autonomous_continuous_learning_v2_40":
        raise ValueError("invalid autonomous learning config schema")
    for key in ("execution_authority",):
        if str(payload.get(key, "NONE")).upper() != "NONE":
            raise ValueError("autonomous learning may not grant execution authority")
    if payload.get("broker_submission_enabled"):
        raise ValueError("broker submission must remain disabled")
    if payload.get("automatic_live_promotion"):
        raise ValueError("automatic live promotion must remain disabled")
    if payload.get("automatic_champion_promotion"):
        raise ValueError("automatic champion promotion must remain disabled")
    payload["_config_path"] = str(config_path)
    return payload


def agent_specs_v240(config: dict) -> tuple[AgentSpecV240, ...]:
    return tuple(AgentSpecV240(**row) for row in config.get("agents", []))


def resolve_runtime_paths_v240(project_root: str | Path, config: dict) -> dict[str, Path]:
    root = Path(project_root).resolve()
    out = {}
    for key, value in dict(config.get("paths") or {}).items():
        p = Path(value)
        out[key] = p if p.is_absolute() else root / p
    required = {"runtime_root", "database", "models", "reports", "lock"}
    missing = required - set(out)
    if missing:
        raise ValueError(f"missing runtime paths: {sorted(missing)}")
    return out


__all__ = ["load_learning_config_v240", "agent_specs_v240", "resolve_runtime_paths_v240"]
