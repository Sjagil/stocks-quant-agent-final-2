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


def _finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--limit", type=int, default=30)
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

    matrix = (
        pd.read_csv(matrix_path)
        if matrix_path.is_file()
        else pd.DataFrame()
    )
    candidates = (
        pd.read_csv(candidates_path)
        if candidates_path.is_file()
        else pd.DataFrame()
    )

    symbols: list[str] = []

    if not matrix.empty:
        preferred = matrix.loc[
            matrix.get(
                "research_opportunity",
                pd.Series(False, index=matrix.index),
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

    if not candidates.empty and len(set(symbols)) < int(args.limit):
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

    market_caps: dict[str, float] = {}

    if not candidates.empty and "market_cap" in candidates:
        for row in candidates.to_dict(orient="records"):
            symbol = str(row.get("symbol") or "").upper()
            value = _finite(row.get("market_cap"))
            if symbol and value is not None and value > 0:
                market_caps[symbol] = value

    frame, audit = run_verification(
        ROOT,
        symbols=selected,
        as_of=args.as_of,
        market_caps=market_caps,
    )

    matrix_symbols = (
        set(
            matrix["symbol"]
            .dropna()
            .astype(str)
            .str.upper()
        )
        if not matrix.empty
        else set()
    )

    if not frame.empty:
        verified_mask = (
            frame["trade_eligible"]
            .fillna(False)
            .astype(bool)
        )
        audit["verified_matrix_candidates"] = int(
            (
                verified_mask
                & frame["symbol"].astype(str).str.upper().isin(matrix_symbols)
            ).sum()
        )
    else:
        audit["verified_matrix_candidates"] = 0

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification"
    )
    output.mkdir(parents=True, exist_ok=True)

    frame.to_csv(
        output / "verification.csv",
        index=False,
    )

    pending = (
        frame.loc[
            frame["status"]
            == "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"
        ].copy()
        if not frame.empty
        else pd.DataFrame()
    )
    pending.to_csv(
        output / "attestation_queue.csv",
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
        "SHARIAH_FINANCIAL_VERIFICATION_V2_8",
        "SYMBOLS",
        audit["symbols"],
        "VERIFIED",
        audit["verified_trade_eligible"],
        "VERIFIED_MATRIX",
        audit["verified_matrix_candidates"],
        "PENDING_ATTESTATION",
        audit["financial_pass_pending_attestation"],
        "INELIGIBLE",
        audit["ineligible"],
        "DATA_INCOMPLETE",
        audit["data_incomplete"],
        "SOURCES",
        json.dumps(
            audit["fundamentals_sources"],
            sort_keys=True,
        ),
    )

    if not frame.empty:
        columns = [
            "symbol",
            "status",
            "business_status",
            "financial_ratio_status",
            "verified_attestation",
            "trade_eligible",
            "debt_to_market_cap",
            "cash_to_market_cap",
            "receivables_to_market_cap",
            "fundamentals_source",
            "provider_error",
        ]
        print(
            frame[
                [column for column in columns if column in frame.columns]
            ].to_string(index=False)
        )

    print("ATTESTATION_QUEUE", len(pending))
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
