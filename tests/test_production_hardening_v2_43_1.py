from __future__ import annotations

import inspect
import json
from pathlib import Path

from stocks.production.ibkr_historical_v2_43_1 import fetch_historical_batch_v2431


def test_historical_reader_defaults_to_small_failure_isolated_chunks():
    sig = inspect.signature(fetch_historical_batch_v2431)
    assert sig.parameters["maximum_symbols_per_request"].default == 2
    assert sig.parameters["retry_failed_symbols"].default is True
    assert sig.parameters["chunk_timeout_seconds"].default < 180


def test_context_config_has_calendar_fallback_and_reference_macro():
    cfg = json.loads(Path("config/market_context_v2_43.json").read_text())
    assert cfg["calendar"]["providers"] == ["eodhd", "finnhub"]
    assert cfg["calendar"]["cache_ttl_hours"] > 0
    assert cfg["reference_macro"]["provider"] == "references/Stocks"
    assert cfg["policy"]["require_fresh_strategy_hydration"] is True


def test_static_paper_and_rl_safety_invariants_remain_locked():
    hardening = json.loads(Path("config/production_hardening_v2_43_1.json").read_text())
    safety = hardening["safety"]
    assert safety["paper_submission_enabled_by_installer"] is False
    assert safety["rl_direct_broker_control"] is False
    assert safety["ppo_weight"] == 0.0
    assert safety["sac_mode"] == "SHADOW_CONTEXT_ONLY"


def test_forward_runner_fail_closes_stale_hydration():
    text = Path("scripts/run_forward_signal_engine.py").read_text()
    assert "hydration_guard_v2431" in text
    assert 'frame["new_entry_ready"] = False' in text
    assert "STRATEGY_HYDRATION_NOT_FRESH" in text


def test_readiness_splits_machine_state_from_current_signal():
    text = Path("src/stocks/production/context_validation_v2_43.py").read_text()
    assert '"system_paper_ready"' in text
    assert '"entry_eligible_now"' in text
    assert '"paper_entry_ready"' in text
    assert "system_ready and all(dynamic_checks.values())" in text


def test_proposal_adapter_uses_system_readiness_not_signal_presence():
    text = Path("src/stocks/production/proposal_adapter_v2_41.py").read_text()
    assert 'data.get("system_paper_ready")' in text
    assert '"SYSTEM_READY_FOR_PAPER"' in text


def test_finbert_is_singleton_per_snapshot_process():
    text = Path("src/stocks/production/market_context_pipeline_v2_43.py").read_text()
    assert "_NLP_SINGLETON" in text
    assert "def _financial_nlp" in text
    assert "nlp = _financial_nlp()" in text
