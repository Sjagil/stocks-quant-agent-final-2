
#!/usr/bin/env python3
from pathlib import Path

from stocks.research.final_strategy_roster import write_final_strategy_roster

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit, path = write_final_strategy_roster(ROOT)
    print(
        "FINAL_STRATEGY_ROSTER",
        "STRATEGIES",
        audit["strategy_count"],
        "BROAD_FINALISTS",
        audit["broadly_validated_finalists"],
        "PENDING_15M",
        audit["pending_15m_champions"],
        "REDUNDANT",
        audit["redundant_alternates"],
        "REJECTED",
        audit["generalization_rejects"],
    )
    if not frame.empty:
        columns = [
            c for c in (
                "hypothesis_id",
                "strategy",
                "family",
                "generalization_status",
                "redundancy_cluster",
                "cluster_champion",
                "roster_status",
            )
            if c in frame.columns
        ]
        print(frame[columns].to_string(index=False))
    print("OUTPUT", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
