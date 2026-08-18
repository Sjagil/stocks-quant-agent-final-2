#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_json(python: Path, code: str) -> dict:
    completed = subprocess.run(
        [str(python), "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    pybroker_python = ROOT / ".venvs/pybroker/bin/python"
    nautilus_python = ROOT / ".venvs/nautilus/bin/python"

    pybroker_code = r'''
import inspect, json
from pybroker import Strategy, StrategyConfig
cfg = inspect.signature(StrategyConfig)
backtest = inspect.signature(Strategy.backtest)
print(json.dumps({
    "strategy_config": str(cfg),
    "backtest": str(backtest),
    "has_bootstrap_kw": "bootstrap" in cfg.parameters,
    "has_bootstrap_samples_kw": "bootstrap_samples" in cfg.parameters,
    "has_calc_bootstrap_kw": "calc_bootstrap" in backtest.parameters,
}))
'''
    nautilus_code = r'''
import json
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.test_kit.providers import TestInstrumentProvider
instrument = TestInstrumentProvider.equity(symbol="AAPL", venue="SIM")
print(json.dumps({
    "test_kit_import": True,
    "backtest_engine_import": BacktestEngine is not None,
    "instrument_id": str(instrument.id),
    "size_precision": int(instrument.size_precision),
}))
'''

    pybroker = run_json(pybroker_python, pybroker_code)
    nautilus = run_json(nautilus_python, nautilus_code)

    print("PYBROKER_API_PROBE", json.dumps(pybroker, sort_keys=True))
    print("NAUTILUS_API_PROBE", json.dumps(nautilus, sort_keys=True))

    pybroker_ok = pybroker["returncode"] == 0
    nautilus_ok = nautilus["returncode"] == 0

    print(
        "CROSS_ENGINE_ADAPTER_COMPAT_V2_17_2",
        "PYBROKER_READY",
        pybroker_ok,
        "NAUTILUS_READY",
        nautilus_ok,
    )
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")

    return 0 if pybroker_ok and nautilus_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
