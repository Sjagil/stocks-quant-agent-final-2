#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from stocks.providers.env import load_project_env
from stocks.providers.http import ProviderHTTPClient
from stocks.research.sec_fundamentals import (
    DEFAULT_FORMS,
    fetch_company_documents,
    fetch_ticker_map,
    sec_user_agent,
)


ROOT = Path(__file__).resolve().parents[1]

KEYWORDS = re.compile(
    r"(debt|borrow|receiv|cash|investment|marketable|securit|lease)",
    re.IGNORECASE,
)


def _eligible_units(
    raw: dict[str, Any],
    *,
    decision_date: date,
) -> Counter[str]:
    counter: Counter[str] = Counter()
    units = raw.get("units") or {}

    for unit, observations in units.items():
        if not isinstance(observations, list):
            continue
        for obs in observations:
            if not isinstance(obs, dict):
                continue
            if str(obs.get("form") or "") not in DEFAULT_FORMS:
                continue
            try:
                filed = pd.Timestamp(str(obs.get("filed"))).date()
                end = pd.Timestamp(str(obs.get("end"))).date()
            except Exception:
                continue
            if filed > decision_date or end > decision_date:
                continue
            counter[str(unit)] += 1

    return counter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()

    decision_date = date.fromisoformat(args.as_of)
    load_project_env(ROOT)

    verification_path = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification/"
        "verification.csv"
    )
    if not verification_path.is_file():
        print("SEC_UNIT_GAPS_V2_11 ERROR VERIFICATION_MISSING")
        return 2

    verification = pd.read_csv(verification_path)
    incomplete = verification.loc[
        verification["status"].astype(str)
        == "SHARIAH_DATA_INCOMPLETE"
    ]
    symbols = sorted(set(incomplete["symbol"].astype(str).str.upper()))

    rows: list[dict[str, Any]] = []
    agent = sec_user_agent()

    with ProviderHTTPClient(user_agent=agent) as client:
        ticker_map = fetch_ticker_map(client, user_agent=agent)

        for symbol in symbols:
            cik = ticker_map.get(symbol)
            if cik is None:
                rows.append(
                    {
                        "symbol": symbol,
                        "status": "SEC_TICKER_MAP_MISSING",
                        "keyword_fact_rows": 0,
                        "usd_rows": 0,
                        "non_usd_rows": 0,
                        "units": "",
                        "currency_conversion_authority": "NONE",
                    }
                )
                continue

            try:
                _submissions, companyfacts = fetch_company_documents(
                    client,
                    cik=cik,
                    user_agent=agent,
                )
            except Exception as exc:
                rows.append(
                    {
                        "symbol": symbol,
                        "status": f"FETCH_ERROR:{type(exc).__name__}",
                        "keyword_fact_rows": 0,
                        "usd_rows": 0,
                        "non_usd_rows": 0,
                        "units": "",
                        "currency_conversion_authority": "NONE",
                    }
                )
                continue

            total = Counter()
            facts_root = companyfacts.get("facts") or {}

            for taxonomy in ("us-gaap", "ifrs-full"):
                for concept, raw in (facts_root.get(taxonomy) or {}).items():
                    if not KEYWORDS.search(str(concept)):
                        continue
                    if not isinstance(raw, dict):
                        continue
                    total.update(
                        _eligible_units(
                            raw,
                            decision_date=decision_date,
                        )
                    )

            usd = int(total.get("USD", 0))
            total_rows = int(sum(total.values()))
            non_usd = total_rows - usd

            rows.append(
                {
                    "symbol": symbol,
                    "status": (
                        "USD_FACTS_AVAILABLE"
                        if usd > 0
                        else (
                            "NON_USD_FACTS_ONLY"
                            if non_usd > 0
                            else "NO_ELIGIBLE_KEYWORD_FACTS"
                        )
                    ),
                    "keyword_fact_rows": total_rows,
                    "usd_rows": usd,
                    "non_usd_rows": non_usd,
                    "units": "|".join(
                        f"{unit}:{count}"
                        for unit, count in sorted(total.items())
                    ),
                    "currency_conversion_authority": "NONE",
                }
            )

    frame = pd.DataFrame(rows)
    output = (
        ROOT
        / "artifacts/research_runtime/"
        "sec_unit_gaps_v2_11"
    )
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "unit_gaps.csv", index=False)

    non_usd_only = int(
        (frame["status"] == "NON_USD_FACTS_ONLY").sum()
    ) if not frame.empty else 0
    no_facts = int(
        (frame["status"] == "NO_ELIGIBLE_KEYWORD_FACTS").sum()
    ) if not frame.empty else 0

    print(
        "SEC_UNIT_GAPS_V2_11",
        "SYMBOLS",
        len(frame),
        "NON_USD_ONLY",
        non_usd_only,
        "NO_FACTS",
        no_facts,
        "AUTO_FX",
        False,
    )
    if not frame.empty:
        print(frame.to_string(index=False))

    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
