import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_config_is_fail_closed_by_default():
    cfg=json.loads((ROOT/'config/production_runtime_v2_41.json').read_text())
    assert cfg['authority']['automatic_live_promotion'] is False
    assert cfg['authority']['automatic_champion_promotion'] is False
    assert cfg['authority']['submission_enabled_by_default'] is False
    assert cfg['eligibility']['allow_rl_direct_broker_control'] is False
    assert cfg['risk']['long_only'] is True
    assert cfg['risk']['whole_shares_only'] is True
    assert cfg['risk']['max_live_canary_notional_eur'] == 0


def test_runtime_does_not_import_rl_policy_for_order_control():
    text=(ROOT/'src/stocks/production/runtime_v2_41.py').read_text()
    assert 'stocks.rl' not in text
    assert 'stable_baselines3' not in text
    assert 'automatic_live_promotion": False' in text


def test_legacy_trade_intent_remains_execution_neutral_when_present():
    path=ROOT/'src/stocks/contracts/trade_intent.py'
    if not path.exists():
        return
    text=path.read_text()
    assert 'execution_authority: str = "NONE"' in text
    assert 'if self.execution_authority != "NONE"' in text
