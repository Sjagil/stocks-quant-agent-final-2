#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("RUN", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    repo = ROOT / "references/Kronos"
    requirements = repo / "requirements.txt"
    if not requirements.is_file():
        raise SystemExit(
            "references/Kronos/requirements.txt missing; clone Kronos first"
        )

    venv = ROOT / ".venvs/kronos"
    if args.recreate and venv.exists():
        import shutil
        shutil.rmtree(venv)

    python = venv / "bin/python"
    if not python.is_file():
        run([sys.executable, "-m", "venv", str(venv)])

    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", str(requirements)])
    run([str(python), "-m", "pip", "install", "pyarrow>=15,<24"])
    run(
        [
            str(python),
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0, {str(repo)!r}); "
                "import pandas, torch, huggingface_hub, safetensors; "
                "from model import Kronos, KronosTokenizer, KronosPredictor; "
                "print('KRONOS_ENV_OK', pandas.__version__, torch.__version__)"
            ),
        ]
    )

    print("KRONOS_ISOLATED_PYTHON", python)
    print("MAIN_VENV_MUTATION False")
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
