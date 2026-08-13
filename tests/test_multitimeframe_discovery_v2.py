from pathlib import Path

import pandas as pd

from stocks.data.multitimeframe import (
    discover_local_frames,
)


def test_discovery_finds_derived_15m(
    tmp_path: Path,
) -> None:
    target = (
        tmp_path
        / "data"
        / "derived"
        / "QQQ_15m.parquet"
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    index = pd.date_range(
        "2026-01-05 14:30",
        periods=20,
        freq="15min",
        tz="UTC",
    )

    frame = pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
        },
        index=index,
    )

    frame.to_parquet(
        target
    )

    frames, paths = (
        discover_local_frames(
            tmp_path,
            "QQQ",
        )
    )

    assert "15m" in frames
    assert paths["15m"] == target
    assert len(frames["15m"]) == 20
