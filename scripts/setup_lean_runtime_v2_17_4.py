#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print("RUN", " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-cli", action="store_true")
    parser.add_argument("--build-launcher", action="store_true")
    args = parser.parse_args()

    lean_repo = ROOT / "references/Lean"
    if not lean_repo.is_dir():
        raise SystemExit("references/Lean missing")

    cli_venv = ROOT / ".venvs/lean-cli"
    cli_python = cli_venv / "bin/python"
    cli_binary = cli_venv / "bin/lean"

    if args.install_cli:
        if not cli_python.is_file():
            run([sys.executable, "-m", "venv", str(cli_venv)])
        run([str(cli_python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(cli_python), "-m", "pip", "install", "--upgrade", "lean"])

    if args.build_launcher:
        dotnet = shutil.which("dotnet")
        if not dotnet:
            raise SystemExit("dotnet unavailable")
        launcher_project = lean_repo / "Launcher/QuantConnect.Lean.Launcher.csproj"
        if not launcher_project.is_file():
            raise SystemExit(f"LEAN launcher project missing: {launcher_project}")
        run(
            [
                dotnet,
                "build",
                str(launcher_project),
                "-c",
                "Release",
                "--nologo",
            ]
        )

    docker = shutil.which("docker")
    docker_ready = False
    if docker:
        probe = subprocess.run(
            [docker, "info"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        docker_ready = probe.returncode == 0

    launcher_candidates = list(
        (lean_repo / "Launcher/bin/Release").glob(
            "**/QuantConnect.Lean.Launcher.dll"
        )
    )

    print("LEAN_CLI_ISOLATED", cli_binary if cli_binary.is_file() else None)
    print("DOCKER", docker)
    print("DOCKER_READY", docker_ready)
    print("DOTNET", shutil.which("dotnet"))
    print(
        "LEAN_LAUNCHER",
        launcher_candidates[0] if launcher_candidates else None,
    )
    print(
        "LEAN_RUNTIME_CANDIDATE",
        bool(
            (cli_binary.is_file() and docker_ready)
            or launcher_candidates
        ),
    )
    print("LEAN_CANONICAL_DATA_ADAPTER_IMPLEMENTED False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
