from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nautilus_normalizer_supports_current_order_report_schema():
    text = (
        ROOT / "scripts/workers/nautilus_crosscheck_worker_v2_17.py"
    ).read_text(encoding="utf-8")

    assert '"ts_last"' in text
    assert '"avg_px"' in text
    assert '"filled_qty"' in text


def test_terminal_docker_uses_colima_not_docker_desktop():
    text = (
        ROOT / "scripts/setup_terminal_docker_v2_17_6.py"
    ).read_text(encoding="utf-8")

    assert '"colima"' in text
    assert '"start"' in text
    assert '"--runtime"' in text
    assert '"docker"' in text
    assert "Docker.app" not in text
    assert "open -a Docker" not in text


def test_terminal_docker_has_no_trading_authority():
    text = (
        ROOT / "scripts/setup_terminal_docker_v2_17_6.py"
    ).read_text(encoding="utf-8")

    assert "BROKER_CALLS 0" in text
    assert "ORDER_CALLS 0" in text
    assert "EXECUTION_AUTHORITY NONE" in text
