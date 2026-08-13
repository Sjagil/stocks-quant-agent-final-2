from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REFERENCE = (
    ROOT
    / "references"
    / "Stocks"
)

FILES = (
    "src/stocks/screener/sources.py",
    "src/stocks/news/intelligence.py",
    "src/stocks/analysis/theme_news.py",
    "src/stocks/research/sec_overlay.py",
    "src/stocks/quant_platform/providers.py",
    "src/stocks/microstructure/orderflow.py",
)


def inspect_file(
    relative: str,
) -> dict:
    path = (
        REFERENCE
        / relative
    )

    result = {
        "path": relative,
        "exists": path.is_file(),
        "functions": [],
        "classes": [],
    }

    if not path.is_file():
        return result

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            result[
                "functions"
            ].append(
                node.name
            )

        elif isinstance(
            node,
            ast.ClassDef,
        ):
            result[
                "classes"
            ].append(
                node.name
            )

    return result


payload = {
    "schema": (
        "stocks_reference_inventory_v1"
    ),
    "repo": str(
        REFERENCE
    ),
    "files": [
        inspect_file(
            relative
        )
        for relative
        in FILES
    ],
}

output = (
    ROOT
    / "artifacts"
    / "source_fabric"
    / "stocks_reference_inventory.json"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output.write_text(
    json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print(
    json.dumps(
        payload,
        indent=2,
    )
)
