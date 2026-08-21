from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from stocks.orchestration.validated_portfolio_gateway_v2_24 import (
    DEFAULT_OUTPUT_ROOT,
    build_dynamic_validated_portfolio_intents_from_project,
    write_dynamic_validated_portfolio_bundle,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--equity-eur", type=float, required=True)
    value.add_argument("--decision-time", default=None)
    return value


def main() -> int:
    args = parser().parse_args()
    decision_time = (
        datetime.fromisoformat(args.decision_time)
        if args.decision_time
        else datetime.now(UTC)
    )
    if decision_time.tzinfo is None:
        raise ValueError("--decision-time must be timezone-aware")
    root = Path.cwd().resolve()
    bundle = build_dynamic_validated_portfolio_intents_from_project(
        root,
        decision_time=decision_time,
        equity_eur=args.equity_eur,
    )
    output = write_dynamic_validated_portfolio_bundle(bundle, root / DEFAULT_OUTPUT_ROOT)
    print(
        "DYNAMIC_VALIDATED_PORTFOLIO_GATEWAY_V2_24",
        "INTENTS", len(bundle.intents),
        "TARGETS", len(bundle.projection.targets),
        "REJECTED", len(bundle.projection.rejected),
    )
    print("TOTAL_WEIGHT", bundle.projection.total_weight)
    print("CASH_WEIGHT", bundle.projection.cash_weight)
    print("BROKER_CALLS", bundle.audit.get("broker_calls", 0))
    print("ORDER_CALLS", bundle.audit.get("order_calls", 0))
    print("EXECUTION_AUTHORITY", bundle.execution_authority)
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
