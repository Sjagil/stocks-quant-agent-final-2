from pathlib import Path

import pandas as pd

from stocks.research.dynamic_universe_generalization import (
    build_universe_plan,
    walkforward_readiness,
)
from stocks.research.eodhd_holdout_hydration import (
    apply_split_adjustments,
    normalize_splits,
)


def test_split_adjustment_is_causal_and_price_consistent():
    index = pd.DatetimeIndex(
        ["2024-01-02T14:30:00Z", "2024-01-03T14:30:00Z"],
        name="timestamp",
    )
    frame = pd.DataFrame(
        {
            "open": [100.0, 25.0],
            "high": [104.0, 26.0],
            "low": [96.0, 24.0],
            "close": [100.0, 25.0],
            "volume": [1000.0, 4000.0],
        },
        index=index,
    )
    payload = {
        "splits": [
            {
                "code": "XYZ.US",
                "split_date": "2024-01-03",
                "old_shares": 1,
                "new_shares": 4,
            }
        ]
    }
    splits = normalize_splits(payload, "XYZ")
    adjusted = apply_split_adjustments(frame, splits)
    assert adjusted.iloc[0]["close"] == 25.0
    assert adjusted.iloc[0]["volume"] == 4000.0
    assert adjusted.iloc[1]["close"] == 25.0


def test_walkforward_readiness_fails_closed_before_split_builder():
    small = pd.DataFrame({"date": range(500)})
    readiness = walkforward_readiness(
        {"XYZ": small},
        min_symbols=5,
        min_rows=4000,
    )
    assert readiness["ready"] is False
    assert readiness["reason"] == "INSUFFICIENT_UNSEEN_SYMBOLS"


def test_holdout_plan_does_not_admit_non_holdout_local_symbols(tmp_path: Path):
    fabric = tmp_path / "data/canonical/provider_fabric"
    fabric.mkdir(parents=True)
    (fabric / "AAPL_1h.parquet").touch()
    (fabric / "HOLD_1h.parquet").touch()
    (fabric / "OTHER_1h.parquet").touch()
    plan = build_universe_plan(
        tmp_path,
        development_symbols={"AAPL"},
        holdout_symbols={"HOLD"},
    )
    rows = {row.symbol: row for row in plan.itertuples(index=False)}
    assert rows["HOLD"].eligible_unseen_1h is True
    assert rows["OTHER"].eligible_unseen_1h is False
    assert rows["AAPL"].eligible_unseen_1h is False


def test_historical_split_string_format_is_supported():
    from stocks.research.eodhd_holdout_hydration import normalize_splits

    rows = normalize_splits(
        [{"date": "2020-08-31", "split": "4.000000/1.000000"}],
        "AAPL",
    )
    assert len(rows) == 1
    assert rows[0]["ratio"] == 4.0
    assert str(rows[0]["split_date"]) == "2020-08-31"

