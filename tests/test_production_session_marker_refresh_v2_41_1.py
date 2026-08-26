from pathlib import Path

import pandas as pd
import pytest

from stocks.production.data_refresh_v2_41 import (
    _session_close_marker_mask,
    validate_provider_quality_audits_v241,
)


def _row(ts, *, px=100.0, volume=None):
    return {
        "timestamp": pd.Timestamp(ts, tz="UTC"),
        "open": px,
        "high": px,
        "low": px,
        "close": px,
        "volume": volume,
    }


def _write_bad(tmp_path: Path, rows):
    frame = pd.DataFrame(rows).set_index("timestamp")
    path = tmp_path / "bad.parquet"
    frame.to_parquet(path)
    return path


def test_exact_1600_et_flat_nan_volume_is_close_marker():
    frame = pd.DataFrame(
        [_row("2026-08-10 20:00:00", px=773.03, volume=None)]
    ).set_index("timestamp")
    mask = _session_close_marker_mask(
        frame,
        timezone_name="America/New_York",
        close_time="16:00",
    )
    assert mask.tolist() == [True]


def test_other_missing_volume_row_is_not_close_marker():
    frame = pd.DataFrame(
        [
            _row("2026-08-10 19:00:00", px=773.03, volume=None),
            {
                **_row("2026-08-10 20:00:00", px=773.03, volume=None),
                "high": 774.00,
            },
        ]
    ).set_index("timestamp")
    mask = _session_close_marker_mask(
        frame,
        timezone_name="America/New_York",
        close_time="16:00",
    )
    assert mask.tolist() == [False, False]


def test_twelve_close_markers_do_not_relax_two_percent_semantic_gate(tmp_path):
    path = _write_bad(
        tmp_path,
        [
            _row(
                f"2026-08-{10+i:02d} 20:00:00",
                px=100.0 + i,
                volume=None,
            )
            for i in range(12)
        ],
    )
    audits = [{
        "ticker": "SPY.US",
        "interval": "1h",
        "rows_raw": 96,
        "rows_clean": 84,
        "rows_dropped": 12,
        "drop_fraction": 0.125,
        "quarantine_path": str(path),
    }]
    out = validate_provider_quality_audits_v241(
        audits,
        semantic_max_drop_fraction=0.02,
        timezone_name="America/New_York",
        close_time="16:00",
    )
    row = out[0]
    assert row["session_close_markers_excluded"] == 12
    assert row["semantic_non_marker_drops"] == 0
    assert row["semantic_non_marker_drop_fraction"] == 0.0


def test_non_marker_quality_still_fails_closed(tmp_path):
    markers = [
        _row(f"2026-08-{10+i:02d} 20:00:00", px=100.0+i, volume=None)
        for i in range(12)
    ]
    non_markers = [
        _row("2026-08-10 19:00:00", px=200.0, volume=None),
        _row("2026-08-11 19:00:00", px=201.0, volume=None),
    ]
    path = _write_bad(tmp_path, markers + non_markers)
    audits = [{
        "ticker": "SPY.US",
        "interval": "1h",
        "rows_raw": 98,
        "rows_clean": 84,
        "rows_dropped": 14,
        "drop_fraction": 14/98,
        "quarantine_path": str(path),
    }]
    with pytest.raises(ValueError, match="semantic provider quality failure"):
        validate_provider_quality_audits_v241(
            audits,
            semantic_max_drop_fraction=0.02,
            timezone_name="America/New_York",
            close_time="16:00",
        )
