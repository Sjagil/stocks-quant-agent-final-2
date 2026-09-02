from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .contracts_v2_40 import ComponentRunV240


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_allowlisted_component_v240(project_root: str | Path, command: list[str], *, timeout: int = 7200) -> ComponentRunV240:
    root = Path(project_root).resolve()
    if not command:
        raise ValueError("empty command")
    executable = Path(command[0]).resolve()
    venv_python = (root / ".venv/bin/python").resolve()
    if executable != venv_python:
        raise ValueError("components must run through repository venv python")
    script = Path(command[1]).resolve() if len(command) > 1 else None
    allowed = {
        (root / "scripts/run_parallel_research.py").resolve(),
        (root / "scripts/run_continuous_quant_research_v2_39_2.py").resolve(),
        (root / "scripts/run_research_evidence_production_v2_39_3.py").resolve(),
        (root / "scripts/run_shadow_lifecycle_v2_37.py").resolve(),
        (root / "scripts/build_mappo_dataset_v2_42.py").resolve(),
        (root / "scripts/run_agent_shadow_advisory_v2_42.py").resolve(),
    }
    if script not in allowed:
        raise ValueError(f"component script not allowlisted: {script}")
    started = now()
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=int(timeout), check=False)
    finished = now()
    return ComponentRunV240(
        component=script.name,
        status="SUCCEEDED" if proc.returncode == 0 else "FAILED",
        returncode=int(proc.returncode),
        stdout_tail=proc.stdout[-12000:],
        stderr_tail=proc.stderr[-12000:],
    )


__all__ = ["run_allowlisted_component_v240"]
