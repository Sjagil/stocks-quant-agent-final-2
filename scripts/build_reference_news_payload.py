from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


def latest_refresh() -> Path:
    paths = sorted(
        (
            ROOT
            / "artifacts"
            / "source_fabric"
            / "refresh"
        ).glob(
            "refresh-*.json"
        )
    )

    if not paths:
        raise FileNotFoundError(
            "no source refresh artifacts"
        )

    return paths[
        -1
    ]


source = latest_refresh()

data = json.loads(
    source.read_text(
        encoding="utf-8"
    )
)

universe = {}
items = []

for symbol, block in (
    data[
        "symbols"
    ].items()
):
    metadata = {
        "name": "",
        "sector": "",
        "industry": "",
        "underlying_commodity": "",
    }

    for result in (
        block[
            "results"
        ]
    ):
        if (
            result[
                "provider"
            ]
            == "yfinance"
            and result[
                "domain"
            ]
            == "fundamentals"
            and result[
                "state"
            ]
            == "OK"
            and result[
                "items"
            ]
        ):
            info = result[
                "items"
            ][
                0
            ]

            metadata[
                "name"
            ] = str(
                info.get(
                    "longName"
                )
                or info.get(
                    "shortName"
                )
                or ""
            )

            metadata[
                "sector"
            ] = str(
                info.get(
                    "sector"
                )
                or ""
            )

            metadata[
                "industry"
            ] = str(
                info.get(
                    "industry"
                )
                or ""
            )

        if (
            result[
                "domain"
            ]
            != "news"
            or result[
                "state"
            ]
            != "OK"
        ):
            continue

        for raw in (
            result[
                "items"
            ]
        ):
            title = str(
                raw.get(
                    "title"
                )
                or ""
            ).strip()

            if not title:
                continue

            items.append(
                {
                    "provider": (
                        result[
                            "provider"
                        ]
                    ),
                    "provider_id": (
                        raw.get(
                            "provider_id"
                        )
                        or raw.get(
                            "article_id"
                        )
                        or raw.get(
                            "id"
                        )
                    ),
                    "published_at": (
                        raw.get(
                            "published_at"
                        )
                        or raw.get(
                            "published"
                        )
                        or raw.get(
                            "datetime"
                        )
                    ),
                    "title": title,
                    "source": (
                        raw.get(
                            "source_name"
                        )
                        or raw.get(
                            "source"
                        )
                        or result[
                            "provider"
                        ]
                    ),
                    "symbols": (
                        raw.get(
                            "symbols"
                        )
                        or [
                            symbol
                        ]
                    ),
                    "sentiment_polarity": (
                        raw.get(
                            "provider_sentiment"
                        )
                    ),
                }
            )

    universe[
        symbol
    ] = metadata

payload = {
    "universe": universe,
    "items": items,
}

output = (
    ROOT
    / "artifacts"
    / "source_fabric"
    / "stocks-reference-news-payload.json"
)

output.write_text(
    json.dumps(
        payload,
        indent=2,
        default=str,
    )
    + "\n",
    encoding="utf-8",
)

print(
    "SOURCE",
    source,
)

print(
    "SYMBOLS",
    len(
        universe
    ),
)

print(
    "ARTICLES",
    len(
        items
    ),
)

print(
    "OUTPUT",
    output,
)
