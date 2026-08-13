from __future__ import annotations

import importlib.util
import json
import os
import platform
from pathlib import Path

from stocks.providers import SOURCES


ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    path = ROOT / ".env"

    if not path.exists():
        return

    for raw in path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)

        os.environ.setdefault(
            key.strip(),
            value.strip()
            .strip('"')
            .strip("'"),
        )


def module_status(name: str) -> bool:
    return (
        importlib.util.find_spec(name)
        is not None
    )


def main() -> int:
    load_env()

    reference = (
        ROOT
        / "references"
        / "Stocks"
    )

    provider_status = {}

    for source in SOURCES:
        provider_status[
            source.name
        ] = {
            "configured": (
                source.configured()
            ),
            "domains": [
                str(domain)
                for domain
                in source.domains
            ],
            "authoritative": (
                source.authoritative
            ),
            "live_context": (
                source.live_context
            ),
        }

    runtime = {
        "yfinance": (
            module_status(
                "yfinance"
            )
        ),
        "pandas_ta_classic": (
            module_status(
                "pandas_ta_classic"
            )
        ),
        "feedparser": (
            module_status(
                "feedparser"
            )
        ),
        "transformers": (
            module_status(
                "transformers"
            )
        ),
        "torch": (
            module_status(
                "torch"
            )
        ),
    }

    stocks_reference = {
        "repo": (
            reference.is_dir()
        ),
        "screener_sources": (
            reference
            / "src"
            / "stocks"
            / "screener"
            / "sources.py"
        ).is_file(),
        "news_intelligence": (
            reference
            / "src"
            / "stocks"
            / "news"
            / "intelligence.py"
        ).is_file(),
        "theme_news": (
            reference
            / "src"
            / "stocks"
            / "analysis"
            / "theme_news.py"
        ).is_file(),
        "sec_overlay": (
            reference
            / "src"
            / "stocks"
            / "research"
            / "sec_overlay.py"
        ).is_file(),
        "quant_providers": (
            reference
            / "src"
            / "stocks"
            / "quant_platform"
            / "providers.py"
        ).is_file(),
    }

    hf_home = os.environ.get(
        "HF_HOME",
        "",
    )

    path_warning = (
        platform.system() == "Darwin"
        and len(hf_home) >= 3
        and hf_home[1:3] == ":\\"
    )

    payload = {
        "schema": (
            "source_health_v1"
        ),
        "platform": (
            platform.system()
        ),
        "providers": (
            provider_status
        ),
        "runtime": runtime,
        "stocks_reference": (
            stocks_reference
        ),
        "warnings": (
            ["windows_hf_path_on_macos"]
            if path_warning
            else []
        ),
        "secrets_printed": False,
    }

    output = (
        ROOT
        / "artifacts"
        / "source_fabric"
        / "health.json"
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
            sort_keys=True,
        )
    )

    print(
        "ARTIFACT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
