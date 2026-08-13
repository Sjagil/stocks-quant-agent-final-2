from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[2]

REFERENCE = (
    ROOT
    / "references"
    / "Stocks"
)

REFERENCE_PYTHON = (
    ROOT
    / ".venvs"
    / "stocks"
    / "bin"
    / "python"
)


def emit(
    payload: dict,
) -> int:
    print(
        json.dumps(
            payload,
            default=str,
        )
    )

    return (
        0
        if payload.get(
            "state"
        )
        == "OK"
        else 1
    )


def run_python(
    code: str,
) -> dict:
    env = {
        key: value
        for key, value
        in os.environ.items()
        if (
            key.startswith(
                "EODHD_"
            )
            or key.startswith(
                "FRED_"
            )
            or key.startswith(
                "IBKR_"
            )
            or key.startswith(
                "OPENEXCHANGE"
            )
            or key.startswith(
                "WM_"
            )
            or key in {
                "TZ",
                "APP_ENV",
                "DB_URL",
            }
        )
    }

    env[
        "PYTHONPATH"
    ] = str(
        REFERENCE / "src"
    )

    completed = subprocess.run(
        [
            str(
                REFERENCE_PYTHON
            ),
            "-c",
            code,
        ],
        cwd=REFERENCE,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    return {
        "returncode": (
            completed.returncode
        ),
        "stdout": (
            completed.stdout
        ),
        "stderr": (
            completed.stderr
        ),
    }


def health() -> dict:
    paths = {
        "repo": REFERENCE.is_dir(),
        "python": (
            REFERENCE_PYTHON
            .is_file()
        ),
        "news": (
            REFERENCE
            / "src/stocks/news/intelligence.py"
        ).is_file(),
        "screener": (
            REFERENCE
            / "src/stocks/screener/sources.py"
        ).is_file(),
        "sec": (
            REFERENCE
            / "src/stocks/research/sec_overlay.py"
        ).is_file(),
        "orderflow": (
            REFERENCE
            / "src/stocks/microstructure/orderflow.py"
        ).is_file(),
    }

    return {
        "state": (
            "OK"
            if all(
                paths.values()
            )
            else "ERROR"
        ),
        "action": "health",
        "paths": paths,
    }


def catalog() -> dict:
    code = r'''
import json

from stocks.news import intelligence as news
from stocks.research import sec_overlay
from stocks.screener import sources
from stocks.microstructure import orderflow

print(json.dumps({
    "news": [
        name for name in dir(news)
        if not name.startswith("__")
    ],
    "sec": [
        name for name in dir(sec_overlay)
        if not name.startswith("__")
    ],
    "screener": [
        name for name in dir(sources)
        if not name.startswith("__")
    ],
    "orderflow": [
        name for name in dir(orderflow)
        if not name.startswith("__")
    ],
}))
'''

    result = run_python(
        code
    )

    if result[
        "returncode"
    ] != 0:
        return {
            "state": "ERROR",
            "action": "catalog",
            **result,
        }

    try:
        data = json.loads(
            result[
                "stdout"
            ].strip()
        )

    except Exception:
        return {
            "state": "ERROR",
            "action": "catalog",
            **result,
        }

    return {
        "state": "OK",
        "action": "catalog",
        "data": data,
    }


def main() -> int:
    if len(
        sys.argv
    ) != 2:
        return emit(
            {
                "state": "ERROR",
                "error": (
                    "action required"
                ),
            }
        )

    action = sys.argv[1]

    if action == "health":
        return emit(
            health()
        )

    if action == "catalog":
        return emit(
            catalog()
        )

    return emit(
        {
            "state": "ERROR",
            "error": (
                f"unknown action: "
                f"{action}"
            ),
        }
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
