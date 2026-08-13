from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.news.evidence import (
    build_news_evidence,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def latest_refresh() -> Path:
    files = sorted(
        (
            ROOT
            / "artifacts"
            / "source_fabric"
            / "refresh"
        ).glob(
            "refresh-*.json"
        )
    )

    if not files:
        raise FileNotFoundError(
            "no source refresh artifacts"
        )

    return files[-1]


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
    )

    args = parser.parse_args()

    source = (
        args.input
        or latest_refresh()
    )

    payload = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    output = {
        "schema": (
            "news_evidence_v1"
        ),
        "source_refresh": (
            str(source)
        ),
        "symbols": {},
        "execution_authority": (
            "NONE"
        ),
    }

    for symbol, block in (
        payload[
            "symbols"
        ].items()
    ):
        raw_news = []

        for result in (
            block[
                "results"
            ]
        ):
            if (
                result[
                    "domain"
                ]
                != "news"
            ):
                continue

            for item in (
                result[
                    "items"
                ]
            ):
                row = dict(
                    item
                )

                row.setdefault(
                    "provider",
                    result[
                        "provider"
                    ],
                )

                row.setdefault(
                    "provider_id",
                    (
                        row.get(
                            "article_id"
                        )
                        or row.get(
                            "id"
                        )
                        or (
                            result[
                                "provider"
                            ]
                            + "-"
                            + str(
                                len(
                                    raw_news
                                )
                            )
                        )
                    ),
                )

                row.setdefault(
                    "url",
                    "",
                )

                row.setdefault(
                    "summary",
                    "",
                )

                row.setdefault(
                    "source_name",
                    row.get(
                        "source",
                        "",
                    ),
                )

                if (
                    "published_at"
                    not in row
                ):
                    continue

                raw_news.append(
                    row
                )

        evidence = (
            build_news_evidence(
                raw_news,
                target_symbol=(
                    symbol
                ),
            )
        )

        output[
            "symbols"
        ][
            symbol
        ] = [
            row.to_dict()
            for row
            in evidence
        ]

    target_dir = (
        ROOT
        / "artifacts"
        / "evidence"
        / "news"
    )

    target_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = (
        target_dir
        / (
            source.stem
            + "-news.json"
        )
    )

    target.write_text(
        json.dumps(
            output,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        target
    )

    for symbol, rows in (
        output[
            "symbols"
        ].items()
    ):
        print(
            symbol,
            "stories=",
            len(
                rows
            ),
        )

        for row in rows[:3]:
            print(
                " ",
                round(
                    row[
                        "evidence_score"
                    ],
                    4,
                ),
                round(
                    row[
                        "sentiment"
                    ],
                    4,
                ),
                row[
                    "providers"
                ],
                row[
                    "title"
                ][
                    :90
                ],
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
