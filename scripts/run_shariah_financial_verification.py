
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.research.shariah_financial_verification import (
    run_verification,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        required=True,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
    )
    args = parser.parse_args()

    matrix_path = (
        ROOT
        / "artifacts/research_runtime/"
        "candidate_strategy_matrix/matrix.csv"
    )
    candidates_path = (
        ROOT
        / "artifacts/research_runtime/"
        "contextual_discovery/candidates.csv"
    )

    symbols: list[str] = []

    if matrix_path.is_file():
        matrix = pd.read_csv(matrix_path)
        if not matrix.empty:
            preferred = matrix.loc[
                matrix.get(
                    "research_opportunity",
                    pd.Series(
                        False,
                        index=matrix.index,
                    ),
                )
                .fillna(False)
                .astype(bool)
            ]
            if preferred.empty:
                preferred = matrix

            symbols.extend(
                preferred["symbol"]
                .dropna()
                .astype(str)
                .str.upper()
                .tolist()
            )

    if (
        candidates_path.is_file()
        and len(set(symbols)) < int(args.limit)
    ):
        candidates = pd.read_csv(candidates_path)
        if "contextual_score" in candidates:
            candidates = candidates.sort_values(
                "contextual_score",
                ascending=False,
            )
        symbols.extend(
            candidates["symbol"]
            .dropna()
            .astype(str)
            .str.upper()
            .tolist()
        )

    selected: list[str] = []
    seen: set[str] = set()

    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        selected.append(symbol)
        if len(selected) >= int(args.limit):
            break

    frame, audit = run_verification(
        ROOT,
        symbols=selected,
        as_of=args.as_of,
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output / "verification.csv",
        index=False,
    )
    (
        output / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "SHARIAH_FINANCIAL_VERIFICATION_V2_7",
        "SYMBOLS",
        audit["symbols"],
        "VERIFIED",
        audit["verified_trade_eligible"],
        "PENDING_ATTESTATION",
        audit["financial_pass_pending_attestation"],
        "INELIGIBLE",
        audit["ineligible"],
        "DATA_INCOMPLETE",
        audit["data_incomplete"],
    )

    if not frame.empty:
        print(
            frame[
                [
                    "symbol",
                    "status",
                    "business_status",
                    "financial_ratio_status",
                    "verified_attestation",
                    "trade_eligible",
                    "debt_to_market_cap",
                    "cash_to_market_cap",
                    "receivables_to_market_cap",
                    "methodology",
                ]
            ].to_string(index=False)
        )

    print(
        "ARTIFACT_ROOT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
