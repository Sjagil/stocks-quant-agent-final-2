#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(label: str, args: list[str], required: bool = False) -> bool:
    print("=" * 78); print("RUN", label)
    completed = subprocess.run([sys.executable, *args], cwd=ROOT, check=False)
    print("RESULT", label, completed.returncode)
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode == 0

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of", required=True)
    a = p.parse_args()
    run("IBKR_DIAGNOSTIC", ["scripts/diagnose_ibkr_v2_10.py"])
    run("SHARIAH_ATTESTATION_QUEUE", ["scripts/build_shariah_attestation_queue_v2_10.py","--as-of",a.as_of], True)
    run("SEC_CONCEPT_GAP_PROFILE", ["scripts/profile_sec_concept_gaps_v2_10.py","--as-of",a.as_of])
    print("=" * 78)
    print("RUNTIME_UNBLOCK_V2_10 COMPLETE")
    print("AUTOMATIC_SHARIAH_ATTESTATIONS", 0)
    print("AUTOMATIC_SEC_CONCEPT_MAPPING", False)
    print("BROKER_ORDER_SUBMISSION", "DISABLED")
    print("EXECUTION_AUTHORITY", "NONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
