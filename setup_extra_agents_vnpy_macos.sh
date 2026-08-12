#!/usr/bin/env bash
set -u

ROOT="${1:-$PWD}"
cd "$ROOT" || exit 1

if [ ! -f "pyproject.toml" ]; then
  echo "ERROR: pass the repository root as the first argument."
  exit 1
fi

PY312="$HOME/.pyenv/versions/3.12.11/bin/python"
PY310="$HOME/.pyenv/versions/3.10.13/bin/python"

if [ ! -x "$PY312" ]; then
  echo "ERROR: Python 3.12.11 not found at $PY312"
  exit 1
fi

mkdir -p references .venvs

clone_repo() {
  local url="$1"
  local dir="$2"
  if [ -d "$dir/.git" ]; then
    echo "EXISTS: $dir"
  elif [ -e "$dir" ]; then
    echo "WARN: $dir exists but is not a git checkout; leaving it untouched."
  else
    git clone --depth 1 "$url" "$dir"
  fi
}

echo "=== Clone MoonDev / VeighNa references ==="
clone_repo "https://github.com/CurvedLightGroup/MoonDev-Trading-Ai-Agents.git" "$ROOT/references/MoonDev-Trading-Ai-Agents"
clone_repo "https://github.com/vnpy/vnpy.git" "$ROOT/references/vnpy"
clone_repo "https://github.com/vnpy/vnpy_ib.git" "$ROOT/references/vnpy_ib"

echo "=== MoonDev isolated environment ==="
if [ -x "$PY310" ]; then
  MOON_ENV="$ROOT/.venvs/moondev"
  if [ ! -x "$MOON_ENV/bin/python" ]; then
    "$PY310" -m venv "$MOON_ENV"
  fi
  "$MOON_ENV/bin/python" -m pip install --upgrade pip setuptools wheel

  if [ -f "$ROOT/references/MoonDev-Trading-Ai-Agents/requirements.txt" ]; then
    if ! "$MOON_ENV/bin/python" -m pip install -r "$ROOT/references/MoonDev-Trading-Ai-Agents/requirements.txt"; then
      echo "WARN: MoonDev's legacy requirements were not fully installable."
      echo "Installing the known-compatible core set instead."
      "$MOON_ENV/bin/python" -m pip install \
        fastapi==0.109.0 \
        uvicorn==0.25.0 \
        python-multipart==0.0.6 \
        jinja2==3.1.2 \
        python-dotenv==1.0.0 \
        requests==2.31.0 \
        PyPDF2==3.0.0 \
        pandas==2.1.0 \
        termcolor==2.3.0 \
        numpy==1.24.0 \
        schedule==1.2.0 \
        python-dateutil==2.8.2 \
        backoff==2.2.1 \
        youtube-transcript-api==0.6.2 \
        openai==1.59.5 || true
      "$MOON_ENV/bin/python" -m pip install -U pandas-ta-classic || true
    fi
  fi
  "$MOON_ENV/bin/python" -m pip install -U pandas-ta-classic || \
    echo "WARN: pandas-ta-classic optional MoonDev compatibility install failed."
else
  echo "WARN: Python 3.10.13 not found. MoonDev repo cloned, runtime not rebuilt."
fi

echo "=== VeighNa isolated environment ==="
VNPY_ENV="$ROOT/.venvs/vnpy"
if [ ! -x "$VNPY_ENV/bin/python" ]; then
  "$PY312" -m venv "$VNPY_ENV"
fi
"$VNPY_ENV/bin/python" -m pip install --upgrade pip setuptools wheel

if command -v brew >/dev/null 2>&1; then
  export HOMEBREW_NO_AUTO_UPDATE=true
  brew list ta-lib >/dev/null 2>&1 || brew install ta-lib
else
  echo "WARN: Homebrew not found. VeighNa may fail to build/import TA-Lib."
fi

VNPY_SRC="$ROOT/references/vnpy"
if [ -f "$VNPY_SRC/pyproject.toml" ]; then
  echo "Installing VeighNa core + vnpy.alpha extras..."
  if ! "$VNPY_ENV/bin/python" -m pip install -e "$VNPY_SRC[alpha]"; then
    echo "WARN: editable VeighNa install failed; trying normal source install."
    "$VNPY_ENV/bin/python" -m pip install "$VNPY_SRC[alpha]" || \
      echo "WARN: VeighNa install failed. Repository remains available as reference."
  fi
fi

echo "vnpy_ib is intentionally reference-only in v0.4.0."
echo "Reason: upstream vnpy_ib pins a protobuf version that may conflict with newer official IBAPI releases."
echo "Your existing official ibapi installation is left untouched."

echo "=== Verify ==="
if [ -x "$ROOT/.venvs/moondev/bin/python" ]; then
  "$ROOT/.venvs/moondev/bin/python" - <<'PY'
import sys
mods = ["pandas", "numpy", "requests", "fastapi", "openai"]
print("MoonDev Python:", sys.version.split()[0])
for mod in mods:
    try:
        m = __import__(mod)
        print("OK MoonDev", mod, getattr(m, "__version__", "import-ok"))
    except Exception as exc:
        print("WARN MoonDev", mod, exc)
PY
fi

"$VNPY_ENV/bin/python" - <<'PY'
import importlib.metadata as metadata
import sys
print("VeighNa Python:", sys.version.split()[0])
try:
    import vnpy
    print("OK vnpy", getattr(vnpy, "__version__", "import-ok"))
    from vnpy.alpha import dataset, model, strategy
    print("OK vnpy.alpha dataset/model/strategy")
except Exception as exc:
    print("WARN VeighNa", exc)
try:
    import ibapi
    print("OK official ibapi", metadata.version("ibapi"))
except Exception as exc:
    print("INFO official ibapi not installed in VeighNa env:", exc)
try:
    print("protobuf", metadata.version("protobuf"))
except Exception:
    pass
PY

"$VNPY_ENV/bin/python" -m pip check || true

echo "=== Existing main project tests ==="
"$ROOT/.venv/bin/python" -m pytest -q || exit 2

echo "EXTRA SETUP COMPLETE"
echo "MoonDev reference: $ROOT/references/MoonDev-Trading-Ai-Agents"
echo "MoonDev env:       $ROOT/.venvs/moondev"
echo "VeighNa reference: $ROOT/references/vnpy"
echo "VeighNa IB ref:    $ROOT/references/vnpy_ib (reference-only)"
echo "VeighNa env:       $ROOT/.venvs/vnpy"
