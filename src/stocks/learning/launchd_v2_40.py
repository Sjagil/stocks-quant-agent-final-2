from __future__ import annotations

import plistlib
from pathlib import Path


LABEL = "com.sjagil.stocksquant.autonomous-learning-v2-40"


def launchagent_path_v240() -> Path:
    return Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"


def install_launchagent_v240(project_root: str | Path, *, interval_seconds: int = 900) -> Path:
    root = Path(project_root).resolve()
    if int(interval_seconds) < 60:
        raise ValueError("launchd interval must be >=60 seconds")
    plist = launchagent_path_v240()
    plist.parent.mkdir(parents=True, exist_ok=True)
    log_root = root / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": LABEL,
        "ProgramArguments": [
            str(root / ".venv/bin/python"),
            str(root / "scripts/run_autonomous_learning_v2_40.py"),
            "watch",
            "--interval-seconds",
            str(int(interval_seconds)),
        ],
        "WorkingDirectory": str(root),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 30,
        "StandardOutPath": str(log_root / "autonomous_learning_v2_40.out.log"),
        "StandardErrorPath": str(log_root / "autonomous_learning_v2_40.err.log"),
        "EnvironmentVariables": {"PYTHONPATH": str(root / "src")},
    }
    with plist.open("wb") as f:
        plistlib.dump(payload, f, sort_keys=True)
    return plist


def uninstall_launchagent_v240() -> Path:
    plist = launchagent_path_v240()
    if plist.exists():
        plist.unlink()
    return plist


__all__ = ["LABEL", "launchagent_path_v240", "install_launchagent_v240", "uninstall_launchagent_v240"]
