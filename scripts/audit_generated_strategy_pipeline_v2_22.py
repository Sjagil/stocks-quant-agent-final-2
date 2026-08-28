#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from stocks.research.generated_strategy_validation_v2_22 import (
    write_generated_strategy_validation_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit, output = write_generated_strategy_validation_audit(ROOT)
    print("=" * 100)
    print(
        "GENERATED_STRATEGY_PIPELINE_V2_22",
        "COMPLETE",
        audit["pipeline_complete"],
    )
    print("QUEUED_STRATEGIES", audit["queued_strategies"])
    print("AUDITED_STRATEGIES", audit["audited_strategies"])
    print("INCOMPLETE_STRATEGIES", audit["incomplete_strategies"])
    print("BROADLY_VALIDATED_FINALISTS", audit["broadly_validated_finalists"])
    print("BLOCKED_GENERALIZATION_DATA", audit["blocked_generalization_data"])
    print("CROSS_ENGINE_REJECTS", audit["cross_engine_rejects"])
    print("GENERALIZATION_REJECTS", audit["generalization_rejects"])
    print("ERRORS", "|".join(audit["errors"]) or "NONE")
    print("AUTOMATIC_FINALIST_PROMOTION", False)
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    if not frame.empty:
        print(
            frame[
                [
                    "hypothesis_id",
                    "strategy",
                    "cross_engine_status",
                    "generalization_status",
                    "promotion_stage",
                    "roster_status",
                    "pipeline_status",
                    "evidence_complete",
                ]
            ].to_string(index=False)
        )
    print("OUTPUT_ROOT", output)
    return 0 if audit["pipeline_complete"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
