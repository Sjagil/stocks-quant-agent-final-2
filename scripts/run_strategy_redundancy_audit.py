#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.research.strategy_redundancy import pairwise_redundancy

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/strategy_redundancy"


def main() -> int:
    trade_sources = [
        ROOT / "artifacts/research_runtime/strategy_factory_1h/survivor_trades.parquet",
        ROOT / "artifacts/research_runtime/indicator_pybroker_crosscheck/survivor_trades.parquet",
    ]
    parts = []
    for path in trade_sources:
        if path.is_file():
            part = pd.read_parquet(path)
            if not part.empty:
                parts.append(part)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    trades = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    pairs = pairwise_redundancy(trades) if not trades.empty else pd.DataFrame(columns=["left", "right", "entry_jaccard", "realized_pnl_correlation", "redundancy_flag"])
    pairs.to_csv(OUTPUT / "pairs.csv", index=False)
    flagged = pairs.loc[pairs.get("redundancy_flag", pd.Series(dtype=bool)).fillna(False)].copy() if not pairs.empty else pairs
    flagged.to_csv(OUTPUT / "flagged_pairs.csv", index=False)
    audit = {
        "schema": "strategy_redundancy_audit_v1",
        "strategies": int(trades["hypothesis_id"].nunique()) if not trades.empty and "hypothesis_id" in trades else 0,
        "pairs": int(len(pairs)),
        "flagged_pairs": int(len(flagged)),
        "promotion_blocking": False,
        "execution_authority": "NONE",
    }
    (OUTPUT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STRATEGY_REDUNDANCY", "STRATEGIES", audit["strategies"], "PAIRS", audit["pairs"], "FLAGGED", audit["flagged_pairs"])
    if not flagged.empty:
        print(flagged.sort_values(["entry_jaccard", "realized_pnl_correlation"], ascending=False).head(30).to_string(index=False))
    print("ARTIFACT_ROOT", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
