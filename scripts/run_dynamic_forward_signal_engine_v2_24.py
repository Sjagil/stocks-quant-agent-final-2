from __future__ import annotations

from pathlib import Path

from stocks.orchestration.dynamic_forward_signal_engine_v2_24 import (
    write_dynamic_validated_forward_signal_state,
)


def main() -> int:
    frame, audit, output = write_dynamic_validated_forward_signal_state(Path.cwd())
    ready = int(frame["new_entry_ready"].astype(bool).sum()) if not frame.empty else 0
    missing = (
        int(frame["fresh_trigger_reason"].fillna("").astype(str).str.contains("ADAPTER_NOT_IMPLEMENTED").sum())
        if not frame.empty and "fresh_trigger_reason" in frame
        else 0
    )
    print(
        "DYNAMIC_FORWARD_SIGNAL_ENGINE_V2_24",
        "ROWS", len(frame),
        "ELIGIBLE_STRATEGIES", audit.get("eligible_strategies", 0),
        "NEW_ENTRY_READY", ready,
        "MISSING_ADAPTER_ROWS", missing,
    )
    print("STRICT_DYNAMIC_DEPLOYMENT_GATE", audit.get("strict_dynamic_deployment_gate"))
    print("BROKER_CALLS", audit.get("broker_calls", 0))
    print("ORDER_CALLS", audit.get("order_calls", 0))
    print("EXECUTION_AUTHORITY", audit.get("execution_authority"))
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
