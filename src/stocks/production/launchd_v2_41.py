from __future__ import annotations

import os
import plistlib
from pathlib import Path

LABEL = "com.sjagil.stocksquant.production-v2-41"


def launchagent_path_v241() -> Path:
    return Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"


def install_launchagent_v241(root: str | Path, *, interval_seconds: int = 300) -> Path:
    root = Path(root).resolve()
    if int(interval_seconds) < 60:
        raise ValueError("production interval must be >=60 seconds")
    python = root / ".venv/bin/python"
    script = root / "scripts/run_production_runtime_v2_41.py"
    if not python.is_file() or not script.is_file():
        raise FileNotFoundError("production python/script missing")
    path = launchagent_path_v241()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": LABEL,
        "ProgramArguments": [str(python), str(script), "watch", "--interval-seconds", str(int(interval_seconds))],
        "WorkingDirectory": str(root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(root / "logs/production_v2_41.out.log"),
        "StandardErrorPath": str(root / "logs/production_v2_41.err.log"),
        "EnvironmentVariables": {
            "PYTHONPATH": str(root / "src"),
            "PATH": os.environ.get("PATH", "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"),
        },
    }
    with path.open("wb") as handle:
        plistlib.dump(payload, handle)
    return path


def uninstall_launchagent_v241() -> None:
    launchagent_path_v241().unlink(missing_ok=True)
