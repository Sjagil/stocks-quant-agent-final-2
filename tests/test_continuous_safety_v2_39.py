import json
from pathlib import Path
from stocks.research.continuous.contracts_v2_39 import EntityV239
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_config_is_research_only():
 c=json.loads((ROOT/'config/continuous_quant_research_v2_39.json').read_text()); assert c['execution_authority']=='NONE'; assert c['automatic_live_promotion'] is False; assert c['automatic_champion_promotion'] is False; assert c['broker_submission_enabled'] is False; assert c['research_compliance_gate_applied'] is False; assert c['order_calls']==0

def test_entity_cannot_grant_authority():
 with pytest.raises(ValueError): EntityV239('x','STRATEGY',execution_authority='LIVE')

def test_new_modules_do_not_call_broker_order_api():
 text='\n'.join(p.read_text() for p in (ROOT/'src/stocks/research/continuous').glob('*.py')); assert 'placeOrder(' not in text; assert 'BROKER_SUBMISSION_ENABLED = True' not in text
