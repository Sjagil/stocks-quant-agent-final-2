#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from stocks.orchestration.runtime_unblock_v2_10 import attestation_template, build_attestation_queue

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", required=True)
    args = p.parse_args()
    source = ROOT / "artifacts/research_runtime/shariah_financial_verification/verification.csv"
    if not source.is_file():
        print("SHARIAH_ATTESTATION_QUEUE_V2_10 ERROR VERIFICATION_MISSING")
        return 2
    verification = pd.read_csv(source)
    queue = build_attestation_queue(verification)
    output = ROOT / "artifacts/research_runtime/shariah_attestation_queue_v2_10"
    output.mkdir(parents=True, exist_ok=True)
    queue_path = output / "queue.csv"
    queue.to_csv(queue_path, index=False)
    template_path = output / "review_template.json"
    template_path.write_text(
        json.dumps(attestation_template(queue, as_of=args.as_of), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print("SHARIAH_ATTESTATION_QUEUE_V2_10", "PENDING", len(queue),
          "AUTOMATIC_ATTESTATIONS", 0, "TRADE_AUTHORITY", "NONE")
    if not queue.empty:
        print(queue[["symbol","debt_to_market_cap","cash_to_market_cap",
                     "receivables_to_market_cap","report_date","filing_date",
                     "fundamentals_source"]].to_string(index=False))
    print("QUEUE", queue_path)
    print("REVIEW_TEMPLATE", template_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
