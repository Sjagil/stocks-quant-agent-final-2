from __future__ import annotations
import argparse, json
from pathlib import Path

from stocks.shadow.ledger_v2_37 import ShadowLedgerV237
from stocks.shadow.reconciliation_v2_37 import reconcile_shadow_ledger
from stocks.shadow.replay_v2_37 import replay_shadow_state

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="artifacts/shadow_lifecycle_v2_37/shadow.sqlite3")
    parser.add_argument("--output", default="artifacts/shadow_lifecycle_v2_37/snapshot.json")
    args = parser.parse_args()
    with ShadowLedgerV237(args.ledger) as ledger:
        reconciliation = reconcile_shadow_ledger(ledger)
        snapshot = replay_shadow_state(ledger)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "reconciliation": reconciliation.as_dict(),
        "snapshot": snapshot.as_dict(),
    }, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("FULL_SHADOW_LIFECYCLE_V2_37", reconciliation.status)
    print("OUTPUT", out)
    print("EXECUTION_AUTHORITY NONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
