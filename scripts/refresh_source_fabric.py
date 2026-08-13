from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from stocks.providers.env import (
    load_project_env,
)
from stocks.providers.fabric import (
    SourceFabric,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def symbols(
    value: str,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            part.strip().upper()
            for part
            in value.split(",")
            if part.strip()
        )
    )


def main() -> int:
    load_project_env(
        ROOT
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        default=(
            "AAPL,AMD,MSFT,NVDA,"
            "SPY,QQQ,GLD,SLV,CPER"
        ),
    )

    parser.add_argument(
        "--include-engines",
        action="store_true",
    )

    args = parser.parse_args()

    fabric = SourceFabric(
        ROOT
    )

    payload = fabric.run(
        symbols(
            args.symbols
        ),
        include_engines=(
            args.include_engines
        ),
    )

    states = Counter()

    provider_states = {}

    for symbol_data in (
        payload[
            "symbols"
        ].values()
    ):
        for result in symbol_data[
            "results"
        ]:
            state = result[
                "state"
            ]

            states[
                state
            ] += 1

            provider = result[
                "provider"
            ]

            provider_states.setdefault(
                provider,
                Counter(),
            )

            provider_states[
                provider
            ][
                state
            ] += 1

    print(
        json.dumps(
            {
                "artifact": (
                    payload[
                        "artifact"
                    ]
                ),
                "symbols": list(
                    payload[
                        "symbols"
                    ]
                ),
                "states": dict(
                    states
                ),
                "providers": {
                    name: dict(
                        counts
                    )
                    for name, counts
                    in provider_states.items()
                },
                "research_engines": (
                    len(
                        payload.get(
                            "research_engines",
                            {}
                        )
                    )
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
