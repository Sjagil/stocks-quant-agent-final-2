# Stocks Quant Agent Final — v0.4.0

A stocks / ETFs / commodity-proxy active-swing **research platform** with canonical market data, isolated external-research engines and an execution-neutral `TradeIntent` boundary.

## Authority is still non-negotiable

None of the new integration workers can create an IBKR order. MoonDev trading agents are never invoked by the worker layer. VeighNa, Qlib, FinRL and Nautilus are research/challenger engines only.

```text
EODHD / FRED / FX
        ↓
canonical market data
        ↓
research engines / ML / RL
        ↓
PortfolioPlan / shadow suggestions
        ↓
TradeIntent (execution_authority = NONE)
        ↓
EXISTING external risk + broker authority
```

## v0.4.0: integration foundation

This version adds three production-oriented foundations:

1. **Versioned integration contracts + registry + runner**
   - `config/integrations.yaml`
   - `src/stocks/integrations/contracts.py`
   - `src/stocks/integrations/registry.py`
   - `src/stocks/integrations/runner.py`
2. **Isolated workers** for VeighNa, Qlib, FinRL, MoonDev and Nautilus.
3. **Canonical market-data schema** shared by EODHD download, corporate-action normalization and later ML/RL pipelines.

The external frameworks stay isolated in `.venvs/*`. The main Python process never reaches into another environment's `site-packages` and never uses `sys.path` hacks to mix environments.

## Integration protocol

Large data moves through Parquet. Control messages move through versioned JSON files:

```text
main .venv
   ↓ WorkerRequest JSON
isolated Python worker
   ↓ WorkerResponse JSON
artifacts/integrations/<request_id>/
   ├── request.json
   ├── response.json
   ├── run_manifest.json
   ├── stdout.log
   └── stderr.log
```

`IntegrationRunner` uses `subprocess.run(..., shell=False)` and a restricted environment allow-list. Every run records the upstream Git commit when the configured repository exists.

### Current worker capabilities

- **VeighNa**: `health`, `catalog`, `alpha158`
- **Qlib**: `health`, `catalog`
- **FinRL**: `health`, `catalog`
- **MoonDev**: `health`, `catalog` — research catalog only; trading-agent execution is deliberately disabled
- **NautilusTrader**: `health`, `catalog`

Run a non-strict health probe:

```bash
python scripts/check_integrations.py
```

Inspect catalogs:

```bash
python scripts/check_integrations.py --catalog
```

Run one explicit worker action through the same contract boundary:

```bash
python scripts/run_integration.py qlib catalog --strict
```

Fail unless every enabled integration reports fully `OK` (including DEGRADED as a failure):

```bash
python scripts/check_integrations.py --strict
```

### VeighNa Alpha158 worker

The VeighNa worker can generate its upstream Alpha158 feature set from a canonical Parquet. Alpha158 requires a `vwap` input. The worker therefore refuses to invent one unless the caller explicitly opts into `close_proxy` or `hlc3_proxy`.

Call it through `IntegrationRunner`, not by importing VeighNa into the main interpreter. A safe feature-only example is included:

```bash
python scripts/run_integration.py vnpy alpha158 \
  --payload-file config/examples/vnpy_alpha158.json \
  --strict
```

The example keeps `include_label=false`. Enabling the upstream forward-looking label is explicit and the worker emits a purge/embargo warning.

## Canonical market-data contract

`src/stocks/data/canonical.py` owns the canonical OHLCV boundary:

- UTC `DatetimeIndex` named `timestamp`;
- required `open/high/low/close/volume`;
- optional `vwap/trades`;
- no silent forward filling;
- no silent corporate-action adjustment;
- duplicate removal is explicit and deterministic;
- validation catches non-positive prices, invalid high/low, negative volume, missing/non-finite values and non-monotonic timestamps;
- metadata sidecars include schema version, source, adjustment policy, SHA-256 and a quality report.

Corporate actions use **split-only price/volume normalization**. Dividends are deliberately not embedded into intraday OHLC because they should later be modeled as explicit cashflows.

## EODHD ingestion

Put the API key only in local `.env`:

```text
EODHD_API_KEY=...
```

Download canonical 1h data:

```bash
python scripts/download_market_data.py \
  --symbols NVDA AAPL MSFT AMD SPY QQQ GLD SLV CPER \
  --exchange US \
  --timeframe 1h \
  --start 2020-10-01
```

Daily data is also supported:

```bash
python scripts/download_market_data.py \
  --symbols NVDA AAPL SPY \
  --exchange US \
  --timeframe 1d \
  --start 2010-01-01
```

Apply EODHD stock splits:

```bash
python scripts/adjust_intraday_splits.py \
  data/processed/NVDA_1h.parquet \
  --ticker NVDA.US
```

Validate the adjusted data:

```bash
python scripts/validate_rl_data.py \
  data/adjusted/NVDA_1h.parquet \
  --max-single-bar-return 0.50
```

## Install

Python 3.11+ is required. On the user's current Mac setup Python 3.12 is the intended runtime.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[rl,dev]'
python -m pytest -q
```

The base package now includes PyYAML and PyArrow because the integration registry and canonical Parquet layer are first-class functionality.

The supplied setup scripts can recreate the broader research environments and reference clones:

```bash
bash setup_quant_stack_macos.sh "$PWD"
bash setup_extra_agents_vnpy_macos.sh "$PWD"
```

## Safe upgrades

`config/integrations.yaml` is intentionally the only place that knows where each isolated interpreter and reference repository lives. That gives an upgrade boundary:

```text
new external package/repo version
        ↓
rebuild/update that isolated .venv
        ↓
python scripts/check_integrations.py --strict
        ↓
project pytest + small research regression
        ↓
promote environment only after pass
```

Do not modify third-party source in `references/` unless an explicit fork/patch is intended. Do not edit `build/lib/stocks`; edit `src/stocks` only.

## RL remains shadow-only

The existing causal long-only RL environment remains available. PPO and SAC training are research-only. A model must never be promoted from a same-dataset train/evaluation run. Purged walk-forward, untouched OOS, multi-seed, cost stress and promotion governance are the next pipeline stage.

## Tests

v0.4 adds deterministic tests for:

- integration JSON contract round-trips;
- integration registry path resolution;
- subprocess runner protocol and run manifests;
- canonical OHLCV validation;
- split-adjustment continuity;
- canonical Parquet hash round-trip when PyArrow is available;
- existing intelligence/RL/TradeIntent behavior.
