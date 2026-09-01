#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
cd "$ROOT"

if [[ ! -f pyproject.toml || ! -f config/production_runtime_v2_41.json ]]; then
  echo "ERROR: pass the stocks-quant-agent-final-2 repository root"
  exit 2
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
STOCKS_REFERENCE_COMMIT="e6f04da8e5afe53b74bf70390e59b06f6ceb624c"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements-production-v2_44.txt
.venv/bin/python -m pip install --no-deps -e .

mkdir -p references .venvs
if [[ ! -d references/Stocks/.git ]]; then
  git clone --depth 1 https://github.com/Sjagil/Stocks.git references/Stocks
fi
if [[ -n "$(git -C references/Stocks status --short)" ]]; then
  echo "ERROR: references/Stocks has local changes; preserve or commit them before bootstrap"
  exit 2
fi
git -C references/Stocks fetch --depth 1 origin "$STOCKS_REFERENCE_COMMIT"
git -C references/Stocks checkout --detach "$STOCKS_REFERENCE_COMMIT"
if [[ ! -f references/Stocks/src/stocks/screener/service.py ]]; then
  echo "ERROR: references/Stocks is missing the required screener implementation"
  exit 2
fi

"$PYTHON_BIN" -m venv .venvs/stocks
.venvs/stocks/bin/python -m pip install --upgrade pip setuptools wheel
.venvs/stocks/bin/python -m pip install -r requirements-stocks-reference-v2_44.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "CREATED .env FROM .env.example"
fi

.venv/bin/python scripts/run_production_runtime_v2_41.py init
.venv/bin/python scripts/run_production_runtime_v2_41.py doctor || true

echo "BOOTSTRAP_PRODUCTION_V2_44_COMPLETE"
echo "NEXT: fill .env, start IBKR paper TWS/Gateway, then rerun doctor"
