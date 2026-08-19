from __future__ import annotations

from pathlib import Path

from stocks.orchestration.dynamic_validated_strategy_deployment_v2_24 import (
    write_dynamic_validated_strategy_deployment,
)


def main() -> int:
    root = Path.cwd().resolve()
    registry, rejected, audit, output = write_dynamic_validated_strategy_deployment(root)
    print(
        "DYNAMIC_VALIDATED_DEPLOYMENT_V2_24",
        "READY", audit["ready"],
        "BROAD_FINALISTS", audit["broad_finalists"],
        "ELIGIBLE", audit["eligible_strategies"],
        "EXCLUDED", audit["excluded_finalists"],
    )
    print("ELIGIBLE_STRATEGIES", "|".join(audit["eligible_strategy_names"]) or "NONE")
    print("EXCLUDED_STRATEGIES", "|".join(audit["excluded_strategy_names"]) or "NONE")
    if not rejected.empty and "blockers" in rejected:
        for row in rejected[["strategy", "hypothesis_id", "blockers"]].to_dict(orient="records"):
            print("EXCLUDED", row["hypothesis_id"], row["strategy"], row["blockers"])
    print("REGISTRY_SHA256", audit["registry_sha256"])
    print("AUTOMATIC_LIVE_PROMOTION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
