from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nautilus_replay_uses_quote_ticks_at_canonical_open():
    text = (
        ROOT
        / "scripts/workers/"
        "nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "QuoteTick" in text
    assert "subscribe_quote_ticks" in text
    assert "bid_price=px" in text
    assert "ask_price=px" in text
    assert "execute_entry" in text
    assert ".shift(1)" in text
    assert (
        "SCHEDULE_DERIVED_EXECUTION_INTENT_AT_OPEN"
        in text
    )


def test_nautilus_replay_does_not_use_bar_callback_execution():
    text = (
        ROOT
        / "scripts/workers/"
        "nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "def on_bar(" not in text
    assert "TimeInForce.AT_THE_OPEN" not in text
    assert "fractional_shares_allowed" in text


def test_lean_worker_has_real_local_launcher_replay():
    text = (
        ROOT
        / "scripts/workers/lean_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "CrossEngineReplayAlgorithmV2177" in text
    assert "dotnet" in text
    assert "QuantConnect.Lean.Launcher.dll" in text
    assert "FULL_ENGINE_REPLAY" in text
    assert "normalized_ledger.parquet" in text
    assert (
        "LOCAL_LAUNCHER_CUSTOM_BASEDATA"
        in text
    )


def test_lean_algorithm_is_execution_only_and_whole_share():
    text = (
        ROOT
        / "scripts/workers/lean_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "AddData<CanonicalReplayPointV2177>" in text
    assert "MarketOrder(" in text
    assert "XENGINE_ENTRY" in text
    assert "XENGINE_EXIT" in text
    assert "FillQuantity" in text
    assert "execution_authority" in text


def test_no_external_engine_receives_live_authority():
    for relative in (
        "scripts/workers/"
        "nautilus_crosscheck_worker_v2_17.py",
        "scripts/workers/lean_worker_v2_17.py",
    ):
        text = (
            ROOT / relative
        ).read_text(encoding="utf-8")
        assert '"execution_authority": "NONE"' in text
        assert '"broker_calls": 0' in text
        assert '"order_calls": 0' in text
