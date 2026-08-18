#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.agents.feature_views import ROLE_COLUMNS

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = json.loads((ROOT / "config/indicator_discovery.json").read_text(encoding="utf-8"))
    templates = list(config.get("templates") or [])
    roster_path = ROOT / "artifacts/research_runtime/final_strategy_roster/roster.csv"
    validated = set()
    roster_rows = 0
    if roster_path.is_file():
        roster = pd.read_csv(roster_path)
        roster_rows = len(roster)
        if "strategy" in roster and "roster_status" in roster:
            selected = roster.loc[
                roster["roster_status"].astype(str) == "BROADLY_VALIDATED_FINALIST"
            ]
            validated = set(selected["strategy"].astype(str))

    rows = [
        {
            "strategy_family": template,
            "discovery_enabled": True,
            "broadly_validated_finalist": template in validated,
            "execution_authority": "NONE",
        }
        for template in templates
    ]
    output = ROOT / "artifacts/research_runtime/strategy_feature_coverage_v2_14"
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output / "strategy_families.csv", index=False)

    print(
        "STRATEGY_FEATURE_COVERAGE_V2_14 DISCOVERY_FAMILIES",
        len(templates),
        "ROSTER_ROWS",
        roster_rows,
        "MATCHED_BROAD_FINALISTS",
        len(validated),
    )
    for row in rows:
        print(
            "FAMILY",
            row["strategy_family"],
            "DISCOVERY",
            row["discovery_enabled"],
            "BROAD_FINALIST",
            row["broadly_validated_finalist"],
        )
    print(
        "AGENT_ROLE_FEATURE_COUNTS DQN",
        len(ROLE_COLUMNS["DQN_TIMING"]),
        "SAC",
        len(ROLE_COLUMNS["SAC_SIZING"]),
        "RISK",
        len(ROLE_COLUMNS["RISK"]),
    )
    print("EXECUTION_AUTHORITY NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
