#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
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


def probe(command: list[str]) -> bool:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--cpu", type=int, default=4)
    parser.add_argument("--memory", type=int, default=8)
    parser.add_argument("--disk", type=int, default=60)
    args = parser.parse_args()

    brew = shutil.which("brew")
    if args.install:
        if not brew:
            raise SystemExit("Homebrew is required for terminal-only Docker setup")
        if not shutil.which("colima"):
            run([brew, "install", "colima"])
        if not shutil.which("docker"):
            run([brew, "install", "docker"])

    colima = shutil.which("colima")
    docker = shutil.which("docker")

    if not colima:
        print("COLIMA None")
        print("NEXT_ACTION brew install colima")
        return 2
    if not docker:
        print("DOCKER_CLI None")
        print("NEXT_ACTION brew install docker")
        return 2

    if args.start and not probe([colima, "status"]):
        command = [
            colima,
            "start",
            "--runtime",
            "docker",
            "--cpu",
            str(args.cpu),
            "--memory",
            str(args.memory),
            "--disk",
            str(args.disk),
        ]
        if platform.system() == "Darwin":
            command.extend(["--vm-type", "vz"])
        run(command)

    colima_ready = probe([colima, "status"])
    docker_ready = probe([docker, "info"])

    print("TERMINAL_DOCKER_BACKEND COLIMA")
    print("COLIMA", colima)
    print("COLIMA_READY", colima_ready)
    print("DOCKER_CLI", docker)
    print("DOCKER_READY", docker_ready)
    print("DOCKER_DESKTOP_REQUIRED False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")

    return 0 if colima_ready and docker_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
