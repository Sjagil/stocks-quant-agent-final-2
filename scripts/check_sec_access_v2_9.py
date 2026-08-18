#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from stocks.providers.env import (
    load_project_env,
)
from stocks.providers.http import (
    ProviderHTTPClient,
)
from stocks.research.sec_fundamentals import (
    fetch_ticker_map,
    sec_user_agent,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    load_project_env(ROOT)

    try:
        agent = sec_user_agent()
    except Exception as exc:
        print(
            "SEC_ACCESS_V2_9",
            "BLOCKED",
            f"{type(exc).__name__}:{exc}",
        )
        return 2

    with ProviderHTTPClient(
        user_agent=agent
    ) as client:
        try:
            tickers = fetch_ticker_map(
                client,
                user_agent=agent,
            )
        except Exception as exc:
            print(
                "SEC_ACCESS_V2_9",
                "FAILED",
                f"{type(exc).__name__}:{exc}",
            )
            return 2

    print(
        "SEC_ACCESS_V2_9",
        "OK",
        "TICKERS",
        len(tickers),
        "USER_AGENT_DECLARED",
        True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
