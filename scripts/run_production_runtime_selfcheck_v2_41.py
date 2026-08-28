#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/production_runtime_v2_41.json').read_text())
runtime=(ROOT/'src/stocks/production/runtime_v2_41.py').read_text()
neutral=(ROOT/'src/stocks/contracts/trade_intent.py').read_text() if (ROOT/'src/stocks/contracts/trade_intent.py').exists() else ''
checks={
  'PRODUCTION_CONTROL_PLANE': (ROOT/'src/stocks/production/runtime_v2_41.py').is_file(),
  'IBKR_ADAPTER': (ROOT/'src/stocks/production/ibkr_adapter_v2_41.py').is_file(),
  'INCREMENTAL_CLOSED_BAR_REFRESH': (ROOT/'src/stocks/production/data_refresh_v2_41.py').is_file(),
  'PERSISTENT_IDEMPOTENCY_LEDGER': (ROOT/'src/stocks/production/state_store_v2_41.py').is_file(),
  'DOUBLE_RECONCILIATION': 'pre_submit_reconciliation' in runtime,
  'DOUBLE_PREFLIGHT': 'pre_submit_preflight' in runtime,
  'RUNTIME_ERROR_SUBMISSION_BLOCK': 'BLOCKED_RUNTIME_ERRORS' in runtime,
  'PROTECTIVE_STOP_REQUIRED': 'submit_protected_buy' in runtime,
  'KILL_SWITCH': (ROOT/'src/stocks/production/authority_v2_41.py').is_file(),
  'RTH_ONLY': cfg['risk']['regular_trading_hours_only'] is True,
  'WHOLE_SHARES_ONLY': cfg['risk']['whole_shares_only'] is True,
  'LONG_ONLY': cfg['risk']['long_only'] is True,
  'RL_DIRECT_BROKER_CONTROL': cfg['eligibility']['allow_rl_direct_broker_control'],
  'AUTOMATIC_CHAMPION_PROMOTION': cfg['authority']['automatic_champion_promotion'],
  'AUTOMATIC_LIVE_PROMOTION': cfg['authority']['automatic_live_promotion'],
  'SUBMISSION_ENABLED_BY_DEFAULT': cfg['authority']['submission_enabled_by_default'],
  'LIVE_CANARY_CAP_CONFIGURED': float(cfg['risk']['max_live_canary_notional_eur']) > 0,
  'LEGACY_TRADE_INTENT_EXECUTION_NEUTRAL': ('execution_authority != "NONE"' in neutral if neutral else True),
}
print(json.dumps(checks,indent=2,sort_keys=True))
assert checks['PRODUCTION_CONTROL_PLANE']
assert checks['IBKR_ADAPTER']
assert checks['INCREMENTAL_CLOSED_BAR_REFRESH']
assert checks['PERSISTENT_IDEMPOTENCY_LEDGER']
assert checks['DOUBLE_RECONCILIATION']
assert checks['DOUBLE_PREFLIGHT']
assert checks['RUNTIME_ERROR_SUBMISSION_BLOCK']
assert checks['PROTECTIVE_STOP_REQUIRED']
assert checks['RTH_ONLY'] and checks['WHOLE_SHARES_ONLY'] and checks['LONG_ONLY']
assert checks['RL_DIRECT_BROKER_CONTROL'] is False
assert checks['AUTOMATIC_CHAMPION_PROMOTION'] is False
assert checks['AUTOMATIC_LIVE_PROMOTION'] is False
assert checks['SUBMISSION_ENABLED_BY_DEFAULT'] is False
print('PRODUCTION_V2_41_SELFCHECK_OK')
