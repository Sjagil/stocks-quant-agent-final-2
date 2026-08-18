#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urlparse
from stocks.orchestration.runtime_unblock_v2_10 import (
    PASS_ATTESTATION_STATUS, current_verification_row, write_json_atomic
)

ROOT = Path(__file__).resolve().parents[1]

def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def main() -> int:
    p = argparse.ArgumentParser(description="Persist an explicitly human-reviewed external Shariah attestation.")
    p.add_argument("--symbol", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--methodology", required=True)
    p.add_argument("--screened-at", required=True)
    p.add_argument("--valid-until", required=True)
    p.add_argument("--evidence-url", required=True)
    p.add_argument("--notes", default="")
    p.add_argument("--confirm", required=True, choices=["I_VERIFIED_SHARIAH_COMPLIANCE"])
    args = p.parse_args()
    symbol = args.symbol.strip().upper()
    current = current_verification_row(ROOT, symbol)
    if current is None:
        print("ATTESTATION_BLOCKED", symbol, "CURRENT_VERIFICATION_MISSING")
        return 2
    if str(current.get("status")) != PASS_ATTESTATION_STATUS:
        print("ATTESTATION_BLOCKED", symbol, "FINANCIAL_SCREEN_NOT_PENDING_ATTESTATION", current.get("status"))
        return 2
    if not _valid_url(args.evidence_url):
        print("ATTESTATION_BLOCKED", symbol, "EVIDENCE_URL_INVALID")
        return 2
    path = ROOT / "config/shariah_verified_attestations_v1.json"
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            print("ATTESTATION_BLOCKED", symbol, "EXISTING_ATTESTATION_FILE_INVALID")
            return 2
    else:
        payload = {"schema": "shariah_verified_attestations_v1", "attestations": {}}
    attestations = payload.setdefault("attestations", {})
    attestations[symbol] = {
        "symbol": symbol,
        "status": "SHARIAH_COMPLIANT",
        "screened_at": args.screened_at,
        "valid_until": args.valid_until,
        "source": args.source.strip(),
        "methodology": args.methodology.strip(),
        "evidence_url": args.evidence_url.strip(),
        "notes": args.notes.strip(),
        "verification_mode": "EXPLICIT_HUMAN_ATTESTATION",
        "automatic_inference": False,
    }
    write_json_atomic(path, payload)
    print("ATTESTATION_SAVED", symbol, "STATUS", "SHARIAH_COMPLIANT",
          "TRADE_ELIGIBILITY_REQUIRES_RERUN", True)
    print("OUTPUT", path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
