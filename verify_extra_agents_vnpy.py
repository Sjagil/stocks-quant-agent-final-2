from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.expanduser().resolve()

    checks = {
        "MoonDev repo": root / "references" / "MoonDev-Trading-Ai-Agents" / ".git",
        "VeighNa repo": root / "references" / "vnpy" / ".git",
        "VeighNa IB reference": root / "references" / "vnpy_ib" / ".git",
        "MoonDev Python": root / ".venvs" / "moondev" / "bin" / "python",
        "VeighNa Python": root / ".venvs" / "vnpy" / "bin" / "python",
    }
    for name, path in checks.items():
        print(f"{name}: {'OK' if path.exists() else 'MISSING'} -> {path}")

    vnpy_py = checks["VeighNa Python"]
    if vnpy_py.exists():
        subprocess.run(
            [
                str(vnpy_py),
                "-c",
                "import importlib.metadata as m; import vnpy; "
                "print('vnpy', getattr(vnpy, '__version__', 'import-ok')); "
                "from vnpy.alpha import dataset, model, strategy; print('vnpy.alpha OK'); "
                "print('ibapi', m.version('ibapi')) if __import__('importlib').util.find_spec('ibapi') else print('ibapi not installed')",
            ],
            check=False,
        )
        subprocess.run([str(vnpy_py), "-m", "pip", "check"], check=False)

    moon_py = checks["MoonDev Python"]
    if moon_py.exists():
        subprocess.run(
            [str(moon_py), "-c", "import pandas, numpy, requests; print('MoonDev core deps OK')"],
            check=False,
        )


if __name__ == "__main__":
    main()
