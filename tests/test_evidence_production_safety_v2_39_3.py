import json
from pathlib import Path


def test_config_remains_research_only():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'config/research_evidence_production_v2_39_3.json').read_text())
    assert cfg['execution_authority']=='NONE'
    assert cfg['broker_submission_enabled'] is False
    assert cfg['automatic_live_promotion'] is False
    assert cfg['automatic_champion_promotion'] is False
    assert cfg['minimum_effective_oos_observations']>=60
    assert cfg['cost_stress']['required_multiplier']>=2


def test_source_has_no_broker_order_authority():
    root=Path(__file__).resolve().parents[1]
    text='\n'.join(p.read_text(errors='ignore') for p in (root/'src/stocks/research/continuous').glob('*v2_39_3.py'))
    assert 'place_order(' not in text
    assert 'submit_order(' not in text
    assert 'EXECUTION_AUTHORITY' not in text or 'NONE' in text
