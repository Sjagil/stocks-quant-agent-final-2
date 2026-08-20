from pathlib import Path

import pandas as pd

from stocks.research.strategy_redundancy import pairwise_redundancy


def test_identical_entry_sets_are_flagged():
    times = pd.date_range("2026-01-01", periods=12, freq="D", tz="UTC")
    rows = []
    for hypothesis in ("A", "B"):
        for i, timestamp in enumerate(times):
            rows.append(
                {
                    "hypothesis_id": hypothesis,
                    "symbol": "XYZ",
                    "entry_time": timestamp,
                    "exit_time": timestamp + pd.Timedelta(hours=2),
                    "gross_return": 0.01 if i % 2 == 0 else -0.005,
                }
            )
    pairs = pairwise_redundancy(pd.DataFrame(rows))
    assert len(pairs) == 1
    assert pairs.iloc[0]["entry_jaccard"] == 1.0
    assert bool(pairs.iloc[0]["redundancy_flag"]) is True


def test_redundancy_audit_includes_generated_strategy_trades():
    root = Path(__file__).resolve().parents[1]
    text = (
        root / "scripts/run_strategy_redundancy_audit.py"
    ).read_text(encoding="utf-8")
    assert "strategy_generation_v2_22/survivor_trades.parquet" in text
