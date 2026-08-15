
#!/usr/bin/env python3
from pathlib import Path

from stocks.research.research_readiness import write_research_readiness

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload, path = write_research_readiness(ROOT)
    print(
        "RESEARCH_READINESS",
        "RESEARCH_COMPLETE",
        payload["research_platform_complete"],
        "CANDIDATES",
        payload["contextual_candidates"],
        "HYDRATED",
        payload["hydrated_current_candidates"],
        "HOLDOUT",
        payload["frozen_holdout_usable"],
        "BROAD_FINALISTS",
        payload["broadly_validated_finalists"],
        "OPPORTUNITIES",
        payload["current_research_opportunities"],
        "LIVE_READY",
        payload["live_trading_ready"],
    )
    print("LIVE_BLOCKERS", "|".join(payload["live_blockers"]))
    print("OUTPUT", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
