#!/usr/bin/env bash
set -u

ROOT="${1:-$PWD}"
cd "$ROOT" || exit 1

if [ ! -f "pyproject.toml" ]; then
  echo "ERROR: run this from the stocks-quant-agent-final-2 repo root, or pass the repo path as the first argument."
  exit 1
fi

PY312="$HOME/.pyenv/versions/3.12.11/bin/python"

if [ ! -x "$PY312" ]; then
  echo "ERROR: Python 3.12.11 not found at $PY312"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  "$PY312" -m venv .venv
fi

MAIN_PY="$ROOT/.venv/bin/python"

echo "MAIN_PY=$MAIN_PY"
"$MAIN_PY" --version

"$MAIN_PY" -m pip install --upgrade pip setuptools wheel

echo "Installing research/validation/portfolio/RL libraries into main .venv..."
"$MAIN_PY" -m pip install --upgrade \
  vectorbt \
  skfolio \
  optuna \
  optuna-integration \
  sb3-contrib \
  lib-pybroker \
  quantstats \
  pyportfolioopt \
  riskfolio-lib \
  statsmodels \
  tsfresh \
  arch \
  pandas-market-calendars \
  yfinance \
  mplfinance \
  ffn

if command -v brew >/dev/null 2>&1; then
  echo "Installing native macOS dependencies with Homebrew..."
  brew list libomp >/dev/null 2>&1 || brew install libomp
  brew list ta-lib >/dev/null 2>&1 || brew install ta-lib
  "$MAIN_PY" -m pip install --upgrade TA-Lib || echo "WARN: TA-Lib Python package install failed; core setup continues."
else
  echo "WARN: Homebrew not found. Skipping libomp/ta-lib native packages."
fi

mkdir -p references
cd references || exit 1

clone_repo() {
  local url="$1"
  local dir="$2"
  if [ -d "$dir/.git" ]; then
    echo "EXISTS: $dir"
  else
    git clone --depth 1 "$url" "$dir"
  fi
}

echo "Cloning reference repositories..."
clone_repo https://github.com/edtechre/pybroker.git pybroker
clone_repo https://github.com/polakowo/vectorbt.git vectorbt
clone_repo https://github.com/skfolio/skfolio.git skfolio
clone_repo https://github.com/optuna/optuna.git optuna
clone_repo https://github.com/Stable-Baselines-Team/stable-baselines3-contrib.git stable-baselines3-contrib
clone_repo https://github.com/microsoft/qlib.git qlib
clone_repo https://github.com/AI4Finance-Foundation/FinRL-Trading.git FinRL-Trading
clone_repo https://github.com/nautechsystems/nautilus_trader.git nautilus_trader
clone_repo https://github.com/QuantConnect/Lean.git Lean

cd "$ROOT" || exit 1
mkdir -p .venvs

make_env() {
  local name="$1"
  local envdir="$ROOT/.venvs/$name"
  if [ ! -x "$envdir/bin/python" ]; then
    "$PY312" -m venv "$envdir"
  fi
  "$envdir/bin/python" -m pip install --upgrade pip setuptools wheel
}

echo "Installing Qlib in isolated environment..."
make_env qlib
if ! "$ROOT/.venvs/qlib/bin/python" -m pip install --upgrade pyqlib; then
  echo "WARN: Qlib install failed. Repo was still cloned to references/qlib."
fi

echo "Installing NautilusTrader in isolated environment..."
make_env nautilus
if ! "$ROOT/.venvs/nautilus/bin/python" -m pip install --upgrade nautilus_trader; then
  echo "WARN: NautilusTrader install failed. Repo was still cloned to references/nautilus_trader."
fi

echo "Installing LEAN CLI in isolated environment..."
make_env lean
if ! "$ROOT/.venvs/lean/bin/python" -m pip install --upgrade lean; then
  echo "WARN: LEAN CLI install failed. Repo was still cloned to references/Lean."
fi

echo "Installing FinRL-Trading requirements in isolated environment..."
FINRL_ENV="$ROOT/.venvs/finrl"
if [ ! -x "$FINRL_ENV/bin/python" ]; then
  "$PY312" -m venv "$FINRL_ENV"
fi
"$FINRL_ENV/bin/python" -m pip install --upgrade pip setuptools wheel
if [ -f "$ROOT/references/FinRL-Trading/requirements.txt" ]; then
  if ! "$FINRL_ENV/bin/python" -m pip install -r "$ROOT/references/FinRL-Trading/requirements.txt"; then
    echo "WARN: FinRL-Trading dependency install failed. Repo remains available as a reference."
  fi
else
  echo "WARN: FinRL-Trading requirements.txt not found."
fi

echo "Running project tests..."
cd "$ROOT" || exit 1
"$MAIN_PY" -m pytest -q

echo "Verifying main research stack..."
"$MAIN_PY" - <<'PY'
import importlib

mods = {
    "vectorbt": "vectorbt",
    "skfolio": "skfolio",
    "optuna": "optuna",
    "sb3_contrib": "sb3_contrib",
    "pybroker": "pybroker",
    "quantstats": "quantstats",
    "PyPortfolioOpt": "pypfopt",
    "Riskfolio-Lib": "riskfolio",
    "statsmodels": "statsmodels",
    "tsfresh": "tsfresh",
    "arch": "arch",
    "pandas_market_calendars": "pandas_market_calendars",
    "mplfinance": "mplfinance",
    "ffn": "ffn",
}
failed = []
for label, mod in mods.items():
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, "__version__", "import-ok")
        print(f"OK {label}: {ver}")
    except Exception as exc:
        failed.append((label, str(exc)))
        print(f"FAIL {label}: {exc}")

try:
    import talib
    print(f"OK TA-Lib: {getattr(talib, '__version__', 'import-ok')}")
except Exception as exc:
    print(f"OPTIONAL FAIL TA-Lib: {exc}")

if failed:
    print("MAIN_STACK_FAILURES:")
    for label, err in failed:
        print(f"  {label}: {err}")
    raise SystemExit(2)
PY

echo
echo "SETUP COMPLETE"
echo "Main research env:  $ROOT/.venv"
echo "Qlib env:           $ROOT/.venvs/qlib"
echo "Nautilus env:       $ROOT/.venvs/nautilus"
echo "LEAN CLI env:       $ROOT/.venvs/lean"
echo "FinRL-X env:        $ROOT/.venvs/finrl"
echo "Reference repos:    $ROOT/references"
