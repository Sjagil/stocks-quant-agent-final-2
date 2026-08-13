from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def latest_refresh() -> Path:
    paths = sorted(
        (
            ROOT
            / "artifacts"
            / "source_fabric"
            / "refresh"
        ).glob("refresh-*.json")
    )

    if not paths:
        raise FileNotFoundError(
            "no source refresh artifacts"
        )

    return paths[-1]


def main() -> int:
    source = latest_refresh()

    payload = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    universe = {}
    articles = []

    for symbol, block in (
        payload.get("symbols", {}).items()
    ):
        symbol = str(
            symbol
        ).upper()

        metadata = {
            "name": "",
            "sector": "",
            "industry": "",
            "underlying_commodity": "",
        }

        for result in block.get(
            "results",
            [],
        ):
            provider = str(
                result.get("provider") or ""
            )

            domain = str(
                result.get("domain") or ""
            )

            state = str(
                result.get("state") or ""
            )

            items = result.get(
                "items"
            ) or []

            if (
                provider == "yfinance"
                and domain == "fundamentals"
                and state == "OK"
                and items
            ):
                info = dict(
                    items[0]
                )

                metadata["name"] = str(
                    info.get("longName")
                    or info.get("shortName")
                    or ""
                )

                metadata["sector"] = str(
                    info.get("sector")
                    or ""
                )

                metadata["industry"] = str(
                    info.get("industry")
                    or ""
                )

            if (
                domain != "news"
                or state != "OK"
            ):
                continue

            for raw in items:
                if not isinstance(
                    raw,
                    dict,
                ):
                    continue

                title = " ".join(
                    str(
                        raw.get("title")
                        or ""
                    ).split()
                )

                if not title:
                    continue

                summary = " ".join(
                    str(
                        raw.get("summary")
                        or raw.get("description")
                        or ""
                    ).split()
                )

                articles.append(
                    {
                        "provider": provider,
                        "provider_id": (
                            raw.get("provider_id")
                            or raw.get("article_id")
                            or raw.get("id")
                        ),
                        "published_at": (
                            raw.get("published_at")
                            or raw.get("published")
                            or raw.get("datetime")
                        ),
                        "title": title,
                        "summary": summary,
                        "source": (
                            raw.get("source_name")
                            or raw.get("source")
                            or provider
                        ),
                        "provider_symbols": (
                            raw.get("symbols")
                            or []
                        ),
                        "query_symbol": symbol,
                        "sentiment_polarity": (
                            raw.get(
                                "provider_sentiment"
                            )
                        ),
                    }
                )

        universe[symbol] = metadata

    output = (
        ROOT
        / "artifacts"
        / "source_fabric"
        / "stocks-reference-news-payload.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "universe": universe,
                "items": articles,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print("SOURCE", source)
    print("SYMBOLS", len(universe))
    print("ARTICLES", len(articles))
    print("OUTPUT", output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
