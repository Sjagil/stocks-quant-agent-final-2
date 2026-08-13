from __future__ import annotations

import os
from pathlib import Path


def load_project_env(
    project_root: str | Path,
) -> None:
    path = Path(project_root) / ".env"

    if not path.is_file():
        return

    for raw in path.read_text(
        encoding="utf-8",
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        os.environ.setdefault(
            key.strip(),
            value.strip()
            .strip('"')
            .strip("'"),
        )


def secret(
    *names: str,
) -> str:
    for name in names:
        value = os.environ.get(
            name,
            "",
        ).strip()

        if value:
            return value

    return ""
