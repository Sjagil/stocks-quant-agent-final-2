
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.providers.env import load_project_env, secret
from stocks.providers.http import ProviderHTTPClient
from stocks.research.eodhd_holdout_hydration import hydrate_symbol
from stocks.research.shariah_research_precheck import business_precheck


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "artifacts/research_runtime/contextual_discovery/candidates.csv"
OUTPUT = ROOT / "artifacts/research_runtime/contextual_1h_hydration"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--target-usable", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=30)
    parser.add_argument("--start", default="2020-10-01")
    parser.add_argument("--minimum-rows", type=int, default=4000)
    parser.add_argument("--minimum-coverage", type=float, default=0.90)
    args = parser.parse_args()

    OUTPUT.mkdir(parents=True, exist_ok=True)

    if not INPUT.is_file():
        print("CONTEXTUAL_1H_HYDRATION SKIP NO_CANDIDATE_ARTIFACT")
        return 0

    candidates = pd.read_csv(INPUT)
    if candidates.empty or "symbol" not in candidates:
        print("CONTEXTUAL_1H_HYDRATION SKIP ZERO_CANDIDATES")
        return 0

    sort_columns = [
        c for c in (
            "contextual_score",
            "research_score",
            "technical_score",
        )
        if c in candidates.columns
    ]
    if sort_columns:
        candidates = candidates.sort_values(
            sort_columns,
            ascending=[False] * len(sort_columns),
        )

    queue_rows = []
    for row in candidates.to_dict(orient="records"):
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        precheck = business_precheck(
            sector=row.get("sector"),
            industry=row.get("industry"),
            name=row.get("name"),
        )
        queue_rows.append(
            {
                "symbol": symbol,
                "contextual_score": row.get("contextual_score"),
                "research_lane": (
                    row.get("research_lane")
                    or row.get("lane")
                ),
                "shariah_gate": row.get("shariah_gate"),
                "business_precheck": precheck["status"],
                "business_hard_matches": "|".join(precheck["hard_matches"]),
                "business_review_matches": "|".join(precheck["review_matches"]),
                "eligible_for_hydration": (
                    precheck["status"] != "HARD_EXCLUSION_CANDIDATE"
                ),
                "execution_authority": "NONE",
            }
        )

    queue = (
        pd.DataFrame(queue_rows)
        .drop_duplicates("symbol", keep="first")
        .reset_index(drop=True)
    )
    queue.to_csv(OUTPUT / "candidate_queue.csv", index=False)

    load_project_env(ROOT)
    api_key = secret(
        "EODHD_API_KEY",
        "EOD_API_KEY",
        "EODHISTORICALDATA_API_KEY",
    )
    if not api_key:
        print("CONTEXTUAL_1H_HYDRATION SKIP EODHD_KEY_MISSING")
        return 0

    results = []
    usable = 0
    attempts = 0

    http = ProviderHTTPClient(
        user_agent="stocks-quant-agent/contextual-1h-hydration-v2.6"
    )
    try:
        for row in queue.to_dict(orient="records"):
            if usable >= int(args.target_usable):
                break
            if attempts >= int(args.max_attempts):
                break

            if not bool(row["eligible_for_hydration"]):
                results.append(
                    {
                        **row,
                        "status": "SKIPPED_HARD_BUSINESS_EXCLUSION",
                        "rows": 0,
                        "reason": row["business_hard_matches"],
                    }
                )
                continue

            symbol = str(row["symbol"])
            attempts += 1
            try:
                result = hydrate_symbol(
                    ROOT,
                    symbol,
                    start=args.start,
                    as_of=args.as_of,
                    api_key=api_key,
                    minimum_rows=int(args.minimum_rows),
                    minimum_coverage=float(args.minimum_coverage),
                    client=http,
                )
                record = {**row, **result.to_dict()}
                if result.status in {"HYDRATED", "EXISTING_USABLE"}:
                    usable += 1
                print(
                    "CONTEXT_HYDRATE",
                    symbol,
                    result.status,
                    "ROWS",
                    result.rows,
                    "USABLE",
                    usable,
                    "/",
                    args.target_usable,
                )
            except Exception as exc:
                record = {
                    **row,
                    "status": "FAILED",
                    "rows": 0,
                    "first": None,
                    "last": None,
                    "coverage": 0.0,
                    "reason": f"{type(exc).__name__}: {exc}",
                    "execution_authority": "NONE",
                    "broker_calls": 0,
                    "order_calls": 0,
                }
                print("CONTEXT_HYDRATE", symbol, "FAILED", record["reason"])

            results.append(record)
    finally:
        http.close()

    frame = pd.DataFrame(results)
    frame.to_csv(OUTPUT / "hydration_results.csv", index=False)

    if not frame.empty and "status" in frame.columns:
        usable_frame = frame.loc[
            frame["status"].isin(["HYDRATED", "EXISTING_USABLE"])
        ].copy()
    else:
        usable_frame = pd.DataFrame()

    usable_frame.to_csv(OUTPUT / "usable_candidates.csv", index=False)

    audit = {
        "schema": "contextual_1h_hydration_v2_6",
        "queue_count": int(len(queue)),
        "target_usable": int(args.target_usable),
        "attempts": int(attempts),
        "usable": int(len(usable_frame)),
        "target_reached": len(usable_frame) >= int(args.target_usable),
        "hard_business_exclusions": int(
            (
                queue["business_precheck"] == "HARD_EXCLUSION_CANDIDATE"
            ).sum()
        ) if not queue.empty else 0,
        "final_shariah_compliance_claimed": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "CONTEXTUAL_1H_HYDRATION_V2_6",
        "QUEUE",
        audit["queue_count"],
        "ATTEMPTS",
        audit["attempts"],
        "USABLE",
        audit["usable"],
        "TARGET",
        audit["target_usable"],
        "TARGET_REACHED",
        audit["target_reached"],
        "HARD_EXCLUSIONS",
        audit["hard_business_exclusions"],
    )
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
