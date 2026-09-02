from pathlib import Path

import pandas as pd

from stocks.research.research_candidate_registry import _read_optional_csv


def test_optional_csv_accepts_zero_byte_file(tmp_path: Path):
    path = tmp_path / "survivors.csv"
    path.write_bytes(b"")
    frame = _read_optional_csv(path)
    assert isinstance(frame, pd.DataFrame)
    assert frame.empty


def test_optional_csv_accepts_header_only_file(tmp_path: Path):
    path = tmp_path / "survivors.csv"
    path.write_text("symbol,hypothesis_id,status\n", encoding="utf-8")
    frame = _read_optional_csv(path)
    assert list(frame.columns) == ["symbol", "hypothesis_id", "status"]
    assert frame.empty


def test_optional_csv_reads_real_rows(tmp_path: Path):
    path = tmp_path / "survivors.csv"
    path.write_text(
        "symbol,hypothesis_id,status\nSMCI,abc,PROVISIONAL_SURVIVOR\n",
        encoding="utf-8",
    )
    frame = _read_optional_csv(path)
    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "SMCI"
