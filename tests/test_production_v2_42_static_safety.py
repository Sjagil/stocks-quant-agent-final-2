import json
from pathlib import Path


def test_intelligence_config_keeps_agents_off_broker():
    cfg = json.loads(Path("config/production_intelligence_v2_42.json").read_text())
    assert cfg["agents"]["direct_broker_control"] is False
    assert cfg["news"]["require_finbert_for_new_entries"] is True
    assert cfg["strategy_hydration"]["require_all_selected_symbols_fresh"] is True


def test_production_chain_requires_hydration_strategy_portfolio_and_intelligence_in_order():
    text = Path("src/stocks/production/runtime_v2_41.py").read_text()
    labels = [
        "STRATEGY_CANDIDATE_HYDRATION",
        "FORWARD_SIGNAL_ENGINE",
        "PORTFOLIO_DECISION",
        "PRODUCTION_INTELLIGENCE",
    ]
    offsets = [text.index(label) for label in labels]
    assert offsets == sorted(offsets)


def test_production_data_bridge_uses_explicit_30m_alignment_without_relaxing_price_gate():
    cfg = json.loads(Path("config/production_runtime_v2_41.json").read_text())
    assert cfg["data"]["ibkr_history_bar_size"] == "30 mins"
    assert cfg["data"]["ibkr_source_bar_minutes"] == 30
    assert cfg["data"]["production_target_bar_minutes"] == 60
    assert cfg["data"]["maximum_cross_provider_close_disagreement_bps"] == 50.0
    text = Path("src/stocks/production/data_refresh_v2_41_2.py").read_text()
    assert "align_ibkr_rth_to_eodhd_grid_v242" in text
    assert "fetch_historical_batch_v2431" in text


def test_contextual_proposals_are_only_used_when_recent():
    text = Path("src/stocks/production/proposal_adapter_v2_41.py").read_text()
    assert "_contextual_proposal_path_v242" in text
    assert "20 * 60" in text


def test_learning_cycle_builds_mappo_and_runs_agent_shadow_without_execution_authority():
    cfg = json.loads(Path("config/autonomous_continuous_learning_v2_40.json").read_text())
    assert cfg["execution_authority"] == "NONE"
    assert cfg["broker_submission_enabled"] is False
    assert cfg["automatic_live_promotion"] is False
    text = Path("src/stocks/learning/learning_cycle_v2_40.py").read_text()
    assert "mappo_dataset_refresh_every_cycles" in text
    assert "agent_shadow_every_cycles" in text
