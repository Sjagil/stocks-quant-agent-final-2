#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from datetime import date
from pathlib import Path
from typing import Any
import pandas as pd
from stocks.providers.env import load_project_env
from stocks.providers.http import ProviderHTTPClient
from stocks.research.sec_fundamentals import DEFAULT_FORMS, fetch_company_documents, fetch_ticker_map, sec_user_agent

ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = re.compile(r"(debt|borrow|receiv|cash|investment|marketable|securit|financelease)", re.I)

def _latest_observation(raw: dict[str, Any], decision_date: date) -> dict[str, Any] | None:
    candidates = []
    for unit, observations in (raw.get("units") or {}).items():
        if unit != "USD" or not isinstance(observations, list):
            continue
        for obs in observations:
            if not isinstance(obs, dict) or str(obs.get("form") or "") not in DEFAULT_FORMS:
                continue
            try:
                filed = pd.Timestamp(str(obs.get("filed"))).date()
                end = pd.Timestamp(str(obs.get("end"))).date()
            except Exception:
                continue
            if filed > decision_date or end > decision_date:
                continue
            candidates.append({"filed": filed, "end": end, "form": obs.get("form"), "value": obs.get("val")})
    if not candidates:
        return None
    candidates.sort(key=lambda r: (r["end"], r["filed"]))
    return candidates[-1]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", required=True)
    args = p.parse_args()
    decision_date = date.fromisoformat(args.as_of)
    load_project_env(ROOT)
    verification_path = ROOT / "artifacts/research_runtime/shariah_financial_verification/verification.csv"
    if not verification_path.is_file():
        print("SEC_CONCEPT_GAP_PROFILE_V2_10 ERROR VERIFICATION_MISSING")
        return 2
    verification = pd.read_csv(verification_path)
    incomplete = verification.loc[verification["status"].astype(str) == "SHARIAH_DATA_INCOMPLETE"].copy()
    symbols = sorted(set(incomplete["symbol"].astype(str).str.upper())) if not incomplete.empty else []
    output = ROOT / "artifacts/research_runtime/sec_concept_gap_profile_v2_10"
    output.mkdir(parents=True, exist_ok=True)
    rows, errors = [], []
    if symbols:
        agent = sec_user_agent()
        with ProviderHTTPClient(user_agent=agent) as client:
            ticker_map = fetch_ticker_map(client, user_agent=agent)
            for symbol in symbols:
                cik = ticker_map.get(symbol)
                if cik is None:
                    errors.append({"symbol": symbol, "error": "SEC_TICKER_MAP_MISSING"})
                    continue
                try:
                    _, companyfacts = fetch_company_documents(client, cik=cik, user_agent=agent)
                except Exception as exc:
                    errors.append({"symbol": symbol, "error": f"{type(exc).__name__}: {exc}"})
                    continue
                for taxonomy in ("us-gaap", "ifrs-full"):
                    facts = (companyfacts.get("facts") or {}).get(taxonomy) or {}
                    for concept, raw in facts.items():
                        if not KEYWORDS.search(str(concept)) or not isinstance(raw, dict):
                            continue
                        latest = _latest_observation(raw, decision_date)
                        if latest is None:
                            continue
                        rows.append({
                            "symbol": symbol, "taxonomy": taxonomy, "concept": concept,
                            "label": raw.get("label"), "description": raw.get("description"),
                            "latest_end": latest["end"].isoformat(),
                            "latest_filed": latest["filed"].isoformat(),
                            "latest_form": latest["form"], "latest_value": latest["value"],
                            "mapping_authority": "NONE_REVIEW_REQUIRED",
                        })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(["symbol","taxonomy","concept"]).reset_index(drop=True)
    frame.to_csv(output / "concept_candidates.csv", index=False)
    (output / "errors.json").write_text(json.dumps(errors, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SEC_CONCEPT_GAP_PROFILE_V2_10", "SYMBOLS", len(symbols),
          "CONCEPT_ROWS", len(frame), "ERRORS", len(errors),
          "AUTOMATIC_MAPPING", False)
    print("OUTPUT", output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
