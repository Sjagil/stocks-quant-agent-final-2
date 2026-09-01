from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stocks.production.screener_v2_44 import (
    load_production_screener_config_v244,
    production_screener_allows_symbol_v244,
    rank_production_screener_rows_v244,
)

ROOT = Path(__file__).resolve().parents[1]


def row(
    symbol: str,
    *,
    lane: str = "CORE",
    sector: str = "Technology",
    age_date: str = "2026-08-31",
):
    return {
        "code": symbol,
        "name": f"{symbol} Incorporated",
        "exchange": "US",
        "sector": sector,
        "industry": "Software Infrastructure",
        "last_day_data_date": age_date,
        "adjusted_close": 50.0,
        "refund_1d_p": 2.0,
        "refund_5d_p": 6.0,
        "market_capitalization": 12_000_000_000,
        "earnings_share": 2.0,
        "avgvol_1d": 2_000_000,
        "avgvol_200d": 1_500_000,
        "_source_lane": lane,
    }


def test_screener_deduplicates_lanes_and_never_grants_authority():
    cfg = load_production_screener_config_v244(ROOT)
    frame, summary = rank_production_screener_rows_v244(
        [row("AAA", lane="CORE"), row("AAA", lane="TACTICAL")],
        cfg,
        now=pd.Timestamp("2026-09-01T23:00:00Z"),
    )
    assert summary.status == "SUCCEEDED"
    assert len(frame) == 1
    assert frame.iloc[0]["matched_lanes"] == "CORE|TACTICAL"
    assert frame.iloc[0]["execution_authority"] == "NONE"
    assert frame.iloc[0]["trade_eligible"] is False or not bool(
        frame.iloc[0]["trade_eligible"]
    )


def test_business_exclusion_is_a_hard_screen_blocker():
    cfg = load_production_screener_config_v244(ROOT)
    frame, _ = rank_production_screener_rows_v244(
        [row("BANK", sector="Financial Services") | {"industry": "Regional Banks"}],
        cfg,
        now=pd.Timestamp("2026-09-01T23:00:00Z"),
    )
    assert not bool(frame.iloc[0]["screen_eligible"])
    assert "SHARIAH_BUSINESS_HARD_EXCLUSION" in frame.iloc[0]["blockers"]


def test_current_screen_gate_fails_closed_and_accepts_eligible_symbol(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/production_screener_v2_44.json").write_text(
        (ROOT / "config/production_screener_v2_44.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    output = tmp_path / "artifacts/production_runtime_v2_44/screener"
    output.mkdir(parents=True)
    (output / "summary.json").write_text(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "fresh": True,
                "screening_date": "2026-08-31",
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame([{"symbol": "AAA", "screen_eligible": True}]).to_csv(
        output / "candidates.csv", index=False
    )
    assert production_screener_allows_symbol_v244(
        tmp_path, "AAA", now=pd.Timestamp("2026-09-01T23:00:00Z")
    )[0]
    assert not production_screener_allows_symbol_v244(
        tmp_path, "BBB", now=pd.Timestamp("2026-09-01T23:00:00Z")
    )[0]
