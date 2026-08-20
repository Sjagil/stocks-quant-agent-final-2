#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.research.pit_shariah_eligibility_v2_25 import (
    PITHistoricalEligibilityPolicyV225,
    attach_pit_shariah_to_training_frame_v225,
    build_historical_pit_shariah_ledger_v225,
    write_pit_shariah_bundle_v225,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/training/pit_shariah_v2_25"


def _read(path: str) -> pd.DataFrame:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() == ".parquet":
        return pd.read_parquet(source)
    return pd.read_csv(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", required=True, help="CSV/parquet with symbol,decision_time")
    parser.add_argument("--financial-events", required=True)
    parser.add_argument("--market-cap-events", required=True)
    parser.add_argument("--business-events", required=True)
    parser.add_argument("--attestation-events", required=True)
    parser.add_argument("--training-frame")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    config = json.loads((ROOT / "config/pit_shariah_portfolio_v2_25_26.json").read_text(encoding="utf-8"))
    sh = config["shariah"]
    policy = PITHistoricalEligibilityPolicyV225(
        debt_to_market_cap_max=float(sh["debt_to_market_cap_max"]),
        cash_to_market_cap_max=float(sh["cash_and_interest_securities_to_market_cap_max"]),
        receivables_to_market_cap_max=float(sh["receivables_to_market_cap_max"]),
        maximum_attestation_age_days=int(sh["maximum_attestation_age_days"]),
        date_only_availability_lag_days=int(sh["date_only_availability_lag_days"]),
        require_business_state=bool(sh["historical_business_state_required"]),
        require_market_cap=bool(sh["historical_market_cap_required"]),
        require_verified_attestation=bool(sh["verified_attestation_required"]),
    )
    bundle = build_historical_pit_shariah_ledger_v225(
        _read(args.decisions),
        financial_events=_read(args.financial_events),
        market_cap_events=_read(args.market_cap_events),
        business_events=_read(args.business_events),
        attestation_events=_read(args.attestation_events),
        policy=policy,
    )
    output = write_pit_shariah_bundle_v225(bundle, args.output)
    if args.training_frame:
        attached = attach_pit_shariah_to_training_frame_v225(
            _read(args.training_frame),
            bundle.ledger,
        )
        attached.to_csv(output / "training_with_pit_shariah.csv", index=False)
    print(
        "PIT_SHARIAH_LEDGER_V2_25",
        "VALID", bundle.audit["valid"],
        "ROWS", bundle.audit["rows"],
        "VERIFIED", bundle.audit["verified_trade_eligible"],
        "FUTURE_EVIDENCE", bundle.audit["future_evidence_rows"],
    )
    print("HISTORICAL_BACKFILL_ALLOWED", False)
    print("AUTOMATIC_ATTESTATION", False)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0 if bundle.audit["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
