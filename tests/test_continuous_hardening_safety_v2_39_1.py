import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_hardened_config_is_fail_closed():
 c=json.loads((ROOT/'config/continuous_quant_research_v2_39_1.json').read_text());assert c['execution_authority']=='NONE';assert c['automatic_live_promotion'] is False;assert c['automatic_champion_promotion'] is False;assert c['broker_submission_enabled'] is False;assert c['order_calls']==0;assert c['health']['minimum_independent_evidence_classes']>=2;assert c['health']['minimum_independent_evidence_sources']>=2;assert c['health']['minimum_cost_stress_multiplier']>=2
def test_new_code_has_no_broker_order_calls():
 text='\n'.join(p.read_text() for p in (ROOT/'src/stocks/research/continuous').glob('*v2_39_1.py'));assert 'placeOrder(' not in text;assert 'EXECUTION_AUTHORITY = "LIVE"' not in text
