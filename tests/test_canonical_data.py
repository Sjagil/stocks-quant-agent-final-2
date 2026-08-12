from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from stocks.data import (
    CanonicalMetadata,
    SplitEvent,
    apply_split_adjustments,
    canonicalize_ohlcv,
    read_canonical_parquet,
    validate_canonical,
    write_canonical_parquet,
)


def sample_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01 14:30", periods=4, freq="h", tz="UTC", name="timestamp")
    return pd.DataFrame(
        {
            "open": [100.0, 102.0, 51.0, 52.0],
            "high": [103.0, 104.0, 52.0, 53.0],
            "low": [99.0, 101.0, 50.0, 51.0],
            "close": [102.0, 103.0, 51.5, 52.5],
            "volume": [1000.0, 1200.0, 2400.0, 2500.0],
        },
        index=index,
    )


def test_split_adjustment_removes_mechanical_half_price_move() -> None:
    frame = sample_frame()
    event = SplitEvent(pd.Timestamp("2024-01-01 16:00", tz="UTC"), 2.0)
    adjusted = apply_split_adjustments(frame, [event])
    assert adjusted.iloc[0]["close"] == pytest.approx(51.0)
    assert adjusted.iloc[0]["volume"] == pytest.approx(2000.0)
    assert adjusted["close"].pct_change().abs().max() < 0.05


def test_canonical_write_read_hash(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    frame = canonicalize_ohlcv(sample_frame())
    target = tmp_path / "NVDA_1h.parquet"
    write_canonical_parquet(
        frame,
        target,
        CanonicalMetadata(symbol="NVDA", timeframe="1h", source="test"),
    )
    restored, metadata = read_canonical_parquet(target, verify_hash=True)
    assert len(restored) == len(frame)
    assert metadata is not None
    assert metadata["schema_version"] == "1.0"
    assert metadata["sha256"]


def test_canonical_validation_rejects_invalid_high() -> None:
    frame = sample_frame()
    frame.loc[frame.index[0], "high"] = 98.0
    with pytest.raises(ValueError):
        validate_canonical(frame)


def test_canonical_validation_does_not_silently_drop_duplicate_rows() -> None:
    frame = sample_frame()
    duplicated = pd.concat([frame, frame.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate_timestamps"):
        validate_canonical(duplicated)
