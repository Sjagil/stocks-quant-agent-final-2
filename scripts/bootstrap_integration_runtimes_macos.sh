#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
cd "$ROOT"

if [ ! -f pyproject.toml ]; then
  echo "ERROR: run from the repository root or pass it as the first argument"
  exit 2
fi

if [ -x .venvs/moondev/bin/python ]; then
  echo "=== MoonDev TA compatibility ==="
  .venvs/moondev/bin/python -m pip install -U pandas-ta-classic
  .venvs/moondev/bin/python - <<'PY'
import pandas_ta_classic as ta
print("MoonDev pandas-ta-classic:", getattr(ta, "__version__", "import-ok"))
PY
fi

if [ -x .venvs/nautilus/bin/python ]; then
  echo "=== NautilusTrader binary wheel ==="
  .venvs/nautilus/bin/python -m pip install -U pip
  if ! .venvs/nautilus/bin/python -m pip install -U \
    --only-binary=:all: \
    --extra-index-url https://packages.nautechsystems.io/simple \
    nautilus_trader; then
    echo "Latest stable binary was not selected; trying known macOS ARM64 CPython 3.12 release 1.227.0"
    .venvs/nautilus/bin/python -m pip install \
      --only-binary=:all: \
      --extra-index-url https://packages.nautechsystems.io/simple \
      'nautilus_trader==1.227.0'
  fi
  .venvs/nautilus/bin/python - <<'PY'
import importlib.metadata as md
import nautilus_trader
print("NautilusTrader:", md.version("nautilus_trader"))
print("Path:", nautilus_trader.__file__)
PY
fi

if [ -x .venvs/finrl/bin/python ]; then
  echo "=== FinRL core check ==="
  .venvs/finrl/bin/python - <<'PY'
mods = ["numpy", "pandas", "sklearn", "scipy", "lightgbm", "xgboost", "torch", "pandas_market_calendars"]
missing = []
for name in mods:
    try:
        module = __import__(name)
        print("OK", name, getattr(module, "__version__", "import-ok"))
    except Exception as exc:
        missing.append((name, str(exc)))
if missing:
    raise SystemExit("Missing FinRL core modules: " + repr(missing))
PY
fi

python scripts/check_integrations.py
python scripts/check_integrations.py --catalog
python -m pytest -q
