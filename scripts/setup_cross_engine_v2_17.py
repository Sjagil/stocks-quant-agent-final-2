#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("RUN", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate-pybroker", action="store_true")
    args = parser.parse_args()

    repo = ROOT / "references/pybroker"
    if not repo.is_dir():
        raise SystemExit("references/pybroker missing")

    venv = ROOT / ".venvs/pybroker"
    if args.recreate_pybroker and venv.exists():
        shutil.rmtree(venv)

    python = venv / "bin/python"
    if not python.is_file():
        run([sys.executable, "-m", "venv", str(venv)])

    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-e", str(repo)])
    run([str(python), "-m", "pip", "install", "pyarrow>=15,<24"])
    run(
        [
            str(python),
            "-c",
            (
                "import pybroker, pandas, pyarrow; "
                "print('PYBROKER_RUNTIME_OK', "
                "getattr(pybroker, '__version__', 'unknown'), "
                "pandas.__version__, pyarrow.__version__)"
            ),
        ]
    )

    nautilus_python = ROOT / ".venvs/nautilus/bin/python"
    print(
        "NAUTILUS_RUNTIME",
        "READY" if nautilus_python.is_file() else "MISSING",
        nautilus_python,
    )

    print("LEAN_CLI", shutil.which("lean"))
    print("DOCKER", shutil.which("docker"))
    print("DOTNET", shutil.which("dotnet"))
    print("PYBROKER_ISOLATED_PYTHON", python)
    print("BROKER_ORDER_SUBMISSION False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
