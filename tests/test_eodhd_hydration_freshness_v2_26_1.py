from __future__ import annotations
from pathlib import Path
import pandas as pd
from stocks.research.eodhd_holdout_hydration import (
    existing_hourly_state,
    expected_latest_closed_nyse_rth_1h_start,
)

def test_date_only_cutoff_targets_same_day_latest_closed_bar():
    assert expected_latest_closed_nyse_rth_1h_start("2026-08-20") == pd.Timestamp("2026-08-20T19:30:00Z")

def test_weekend_cutoff_targets_previous_session():
    assert expected_latest_closed_nyse_rth_1h_start("2026-08-22") == pd.Timestamp("2026-08-21T19:30:00Z")

def _install_existing(tmp_path: Path, monkeypatch, timestamp: str):
    target = tmp_path / "data/canonical/provider_fabric/TEST_1h.parquet"
    target.parent.mkdir(parents=True)
    target.touch()
    monkeypatch.setattr(pd, "read_parquet", lambda _path: pd.DataFrame())
    import stocks.research.strategy_factory_1h as factory
    monkeypatch.setattr(
        factory,
        "prepare_one_hour_frame",
        lambda _raw, _symbol: pd.DataFrame({"date": [pd.Timestamp(timestamp)]}),
    )

def test_six_day_old_file_is_not_operationally_usable(tmp_path, monkeypatch):
    _install_existing(tmp_path, monkeypatch, "2026-08-14T19:30:00Z")
    state = existing_hourly_state(tmp_path, "TEST", minimum_rows=1, as_of="2026-08-20")
    assert state["usable"] is False
    assert state["reason"] == "STALE_EXISTING_LATEST_SESSION_BAR_MISSING"
    assert state["expected_last"] == "2026-08-20T19:30:00+00:00"

def test_latest_session_bar_is_reused(tmp_path, monkeypatch):
    _install_existing(tmp_path, monkeypatch, "2026-08-20T19:30:00Z")
    state = existing_hourly_state(tmp_path, "TEST", minimum_rows=1, as_of="2026-08-20")
    assert state["usable"] is True
    assert state["session_fresh"] is True


def test_provider_lag_status_is_explicit_in_hydration_contract():
    source = Path(
        "src/stocks/research/eodhd_holdout_hydration.py"
    ).read_text(encoding="utf-8")
    assert '"HYDRATED_PROVIDER_LAG"' in source
    assert "PROVIDER_NOT_FINALIZED_TO_EXPECTED_LATEST_CLOSED_BAR" in source


def test_provider_lag_status_is_not_operationally_fresh_contract():
    source = Path(
        "src/stocks/research/eodhd_holdout_hydration.py"
    ).read_text(encoding="utf-8")
    assert '"HYDRATED_PROVIDER_LAG"' in source
    assert "PROVIDER_NOT_FINALIZED_TO_EXPECTED_LATEST_CLOSED_BAR" in source
