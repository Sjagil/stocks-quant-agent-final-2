from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .contracts_v2_41 import ExecutionMode
from .state_store_v2_41 import ProductionStoreV241


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class AuthorityStatus:
    mode: str
    submission_enabled: bool
    submission_environment: str | None
    kill_switch_active: bool
    live_armed: bool
    live_armed_until: str | None
    automatic_live_promotion: bool = False
    automatic_champion_promotion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def configured_mode(store: ProductionStoreV241, cfg: dict[str, Any]) -> ExecutionMode:
    raw = str(store.get("execution_mode", cfg.get("mode", "OBSERVE"))).upper()
    return ExecutionMode(raw)


def set_mode(store: ProductionStoreV241, mode: str) -> ExecutionMode:
    parsed = ExecutionMode(str(mode).upper())
    store.set("execution_mode", parsed.value)
    return parsed


def set_submission(store: ProductionStoreV241, *, enabled: bool, environment: str | None = None) -> None:
    env = str(environment).upper() if environment else None
    if enabled and env not in {"PAPER", "LIVE"}:
        raise ValueError("submission environment must be PAPER or LIVE")
    store.set("submission_enabled", bool(enabled))
    store.set("submission_environment", env if enabled else None)


def arm_live(root: str | Path, cfg: dict[str, Any], *, hours: float | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    max_hours = float(cfg["authority"].get("live_arm_hours", 24))
    requested = max_hours if hours is None else float(hours)
    if requested <= 0 or requested > max_hours:
        raise ValueError(f"live arm hours must be >0 and <= {max_hours}")
    now = utcnow()
    payload = {
        "schema": "live_arm_v2_41",
        "armed_at": now.isoformat(),
        "armed_until": (now + timedelta(hours=requested)).isoformat(),
        "automatic_live_promotion": False,
    }
    _atomic_json(root / cfg["runtime"]["arm_state_path"], payload)
    return payload


def disarm_live(root: str | Path, cfg: dict[str, Any]) -> None:
    path = Path(root).resolve() / cfg["runtime"]["arm_state_path"]
    path.unlink(missing_ok=True)


def live_arm_status(root: str | Path, cfg: dict[str, Any], *, now: datetime | None = None) -> tuple[bool, str | None]:
    path = Path(root).resolve() / cfg["runtime"]["arm_state_path"]
    if not path.is_file():
        return False, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        until = datetime.fromisoformat(str(payload["armed_until"]))
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        current = now or utcnow()
        return bool(current < until), until.astimezone(timezone.utc).isoformat()
    except Exception:
        return False, None


def kill_switch_active(root: str | Path, cfg: dict[str, Any]) -> bool:
    return (Path(root).resolve() / cfg["runtime"]["kill_switch_path"]).exists()


def engage_kill_switch(root: str | Path, cfg: dict[str, Any], reason: str) -> Path:
    path = Path(root).resolve() / cfg["runtime"]["kill_switch_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"engaged_at": utcnow().isoformat(), "reason": str(reason)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def clear_kill_switch(root: str | Path, cfg: dict[str, Any]) -> None:
    (Path(root).resolve() / cfg["runtime"]["kill_switch_path"]).unlink(missing_ok=True)


def authority_status(root: str | Path, cfg: dict[str, Any], store: ProductionStoreV241) -> AuthorityStatus:
    armed, until = live_arm_status(root, cfg)
    return AuthorityStatus(
        mode=configured_mode(store, cfg).value,
        submission_enabled=bool(store.get("submission_enabled", cfg["authority"].get("submission_enabled_by_default", False))),
        submission_environment=store.get("submission_environment", None),
        kill_switch_active=kill_switch_active(root, cfg),
        live_armed=armed,
        live_armed_until=until,
        automatic_live_promotion=False,
        automatic_champion_promotion=False,
    )
