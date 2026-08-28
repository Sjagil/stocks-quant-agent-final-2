from __future__ import annotations
import argparse
import json
from pathlib import Path

from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.execution_simulator_v2_36 import simulate_execution

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON with intent, market_state and gross_edge_bps")
    parser.add_argument("--output", default="artifacts/execution_cost_v2_36/result.json")
    args = parser.parse_args()
    raw = json.loads(Path(args.input).read_text())
    result = simulate_execution(
        OrderIntentV236(**raw["intent"]),
        MarketStateV236(**raw["market_state"]),
        gross_edge_bps=float(raw["gross_edge_bps"]),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("EXECUTION_COST_LIQUIDITY_V2_36 OK")
    print("NET_EDGE_STATUS", result.edge_decision["status"])
    print("OUTPUT", output)
    print("EXECUTION_AUTHORITY", result.execution_authority)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
