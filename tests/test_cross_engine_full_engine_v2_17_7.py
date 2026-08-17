from __future__ import annotations

import runpy
import signal
import subprocess
from pathlib import Path

import pytest

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
    assert "QuantConnect.Algorithm.CSharp.csproj" in text
    assert '"--no-restore"' in text
    assert "lean_algorithm_source.cs" in text


def test_lean_build_failure_reports_stdout_and_stderr():
    text = (
        ROOT
        / "scripts/workers/lean_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "def _process_failure(" in text
    assert '("STDOUT", completed.stdout)' in text
    assert '("STDERR", completed.stderr)' in text
    assert '"LEAN_BUILD_FAILED"' in text
    assert '"NO_PROCESS_OUTPUT"' in text


def test_lean_runtime_uses_noninteractive_regression_results():
    text = (
        ROOT
        / "scripts/workers/lean_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert "RegressionResultHandler" in text
    assert '"close-automatically"' in text
    assert '"POST_REPLAY_SIGKILL_ACCEPTED"' in text


def test_lean_config_value_can_be_inserted_and_updated(
    monkeypatch,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )
    ensure = namespace["_ensure_json_value"]
    config = (
        "{\n"
        '  "environment": "backtesting",\n'
        "}\n"
    )

    inserted = ensure(
        config,
        "close-automatically",
        "true",
    )
    assert (
        '  "close-automatically": true,'
        in inserted
    )

    updated = ensure(
        inserted,
        "close-automatically",
        "false",
    )
    assert updated.count(
        '"close-automatically"'
    ) == 1
    assert (
        '  "close-automatically": false,'
        in updated
    )


def test_lean_accepts_sigkill_only_after_complete_replay(
    monkeypatch,
    tmp_path,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )
    raw_fills = tmp_path / "lean_raw_fills.csv"
    raw_fills.write_text(
        namespace["LEAN_RAW_FILLS_HEADER"]
        + "\nCPER,2020-01-01T00:00:00Z,BUY,10,1\n",
        encoding="utf-8",
    )
    completed = subprocess.CompletedProcess(
        args=["dotnet"],
        returncode=-signal.SIGKILL,
        stdout="\n".join(
            namespace["LEAN_COMPLETION_MARKERS"]
        ),
        stderr="",
    )

    assert namespace[
        "_completed_replay_after_sigkill"
    ](completed, raw_fills) is True


@pytest.mark.parametrize(
    ("stdout", "stderr"),
    [
        ("completed in", "ERROR:: killed"),
        ("Runtime Error: bad", ""),
        ("incomplete output", ""),
    ],
)
def test_lean_rejects_unproven_sigkill(
    monkeypatch,
    tmp_path,
    stdout,
    stderr,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )
    raw_fills = tmp_path / "lean_raw_fills.csv"
    raw_fills.write_text(
        namespace["LEAN_RAW_FILLS_HEADER"]
        + "\nCPER,2020-01-01T00:00:00Z,BUY,10,1\n",
        encoding="utf-8",
    )
    completed = subprocess.CompletedProcess(
        args=["dotnet"],
        returncode=-signal.SIGKILL,
        stdout=stdout,
        stderr=stderr,
    )

    assert namespace[
        "_completed_replay_after_sigkill"
    ](completed, raw_fills) is False


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


def test_lean_custom_data_uses_current_namespace(monkeypatch):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )

    algorithm_source = namespace["ALGORITHM_SOURCE"]
    assert "using QuantConnect.Data;" in algorithm_source
    assert (
        "using QuantConnect.Data.Subscription;"
        not in algorithm_source
    )


def test_lean_algorithm_has_discoverable_full_type(monkeypatch):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )

    expected = (
        "QuantConnect.Algorithm.CSharp."
        "CrossEngineReplayAlgorithmV2177"
    )
    assert namespace["LEAN_ALGORITHM_TYPE"] == expected
    assert (
        "namespace QuantConnect.Algorithm.CSharp\n{"
        in namespace["ALGORITHM_SOURCE"]
    )


def test_lean_on_data_skips_symbols_missing_from_slice(
    monkeypatch,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )

    source = namespace["ALGORITHM_SOURCE"]
    assert "var points =" in source
    assert "points.TryGetValue(" in source
    assert "out var point" in source
    assert (
        "data.Get<CanonicalReplayPointV2177>(\n"
        "                pair.Key)"
        not in source
    )
    assert (
        namespace["LEAN_SPARSE_SLICE_POLICY"]
        == "TRY_GET_VALUE_SKIP_MISSING_SYMBOLS"
    )


def test_lean_sparse_slice_rewrite_fails_closed(
    monkeypatch,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )

    with pytest.raises(
        ValueError,
        match="sparse Slice access marker",
    ):
        namespace["_replace_sparse_slice_access"](
            "public class MissingOnData {}"
        )


def test_lean_algorithm_source_fails_on_missing_marker(
    monkeypatch,
):
    monkeypatch.syspath_prepend(
        str(ROOT / "scripts/workers")
    )
    namespace = runpy.run_path(
        str(
            ROOT
            / "scripts/workers/lean_worker_v2_17.py"
        )
    )

    with pytest.raises(
        ValueError,
        match="namespace marker missing",
    ):
        namespace["_prepare_algorithm_source"](
            "public class MissingMarker {}"
        )


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
