#!/usr/bin/env python3
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config/production_runtime_v2_41.json").read_text())
text_runtime = (root / "src/stocks/production/runtime_v2_41.py").read_text()
text_cli = (root / "scripts/run_production_runtime_v2_41.py").read_text()
text_broker = (root / "src/stocks/production/ibkr_adapter_v2_41.py").read_text()

checks = {
    "HYBRID_REFRESH_IMPORT_RUNTIME": "data_refresh_v2_41_2" in text_runtime,
    "HYBRID_REFRESH_IMPORT_CLI": "data_refresh_v2_41_2" in text_cli,
    "IBKR_HISTORICAL_BARS_METHOD": "def historical_bars(" in text_broker,
    "CURRENT_SESSION_PROVIDER_IBKR": cfg["data"].get("production_current_session_provider") == "IBKR",
    "CROSS_PROVIDER_OVERLAP_REQUIRED": int(cfg["data"].get("minimum_cross_provider_overlap_bars", 0)) >= 3,
    "ALL_SYMBOL_FRESHNESS_REQUIRED": cfg["data"].get("require_all_symbols_fresh") is True,
    "BROKER_SUBMISSION_DEFAULT_FALSE": cfg["authority"].get("submission_enabled_by_default") is False,
    "AUTOMATIC_LIVE_PROMOTION_FALSE": cfg["authority"].get("automatic_live_promotion") is False,
    "RL_DIRECT_BROKER_CONTROL_FALSE": cfg["eligibility"].get("allow_rl_direct_broker_control") is False,
}
for k, v in checks.items():
    print(k, bool(v))
if not all(checks.values()):
    raise SystemExit(2)
print("PRODUCTION_DATA_BRIDGE_V2_41_2_SELFCHECK_OK")
