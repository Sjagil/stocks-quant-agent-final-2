# Stocks Quant Agent Final v0.4.5

A stocks / ETFs / commodity-proxy active-swing **research platform** with canonical market data, isolated external-research engines and an execution-neutral `TradeIntent` boundary.

## Production quickstart

The production-hardening branch has one supported macOS bootstrap path. It installs the production dependencies, the isolated `Stocks` reference runtime, the EODHD production screener and the fail-closed IBKR PAPER control plane.

```bash
git switch feature/production-hardening-v2-43-1
bash scripts/bootstrap_production_v2_44.sh
```

Then fill `.env` and follow `docs/PRODUCTION_QUICKSTART_V2_44.md`. The screener is mandatory for new entries but has no strategy or order authority.

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

## v0.4.5: operational v2.21 RL and MARL pipeline

v0.4.5 completes the research path from canonical multi-symbol OHLCV to
point-in-time episodes, purged walk-forward training, safe checkpoints, OOS
cost stress, promotion evidence, and independent artifact verification.

The supported v2.21 algorithms are MAPPO and MATD3. The configured final matrix
uses exactly ten seeds. Smoke mode uses one seed and one fold and is explicitly
not promotion-capable.

```bash
python scripts/run_rl_marl_finalization_v2_21.py
python scripts/run_rl_marl_finalization_v2_21.py --full --full-tests
```

All outputs stay research-only and report zero broker calls, zero order calls,
and `EXECUTION_AUTHORITY NONE`.

## v0.4.4: v2.19 validated research automation

v2.19 connects the immutable v2.18 handoff to the forward-signal engine without
granting broker or order authority. It requires the exact two-strategy handoff,
matches each strategy to a broadly validated finalist, canonicalizes and hashes
its frozen parameters, and admits only supported deployment adapters.

The automation is deterministic and fail-closed. It verifies all v2.18 source
hashes on every run, rejects overlapping runs, recovers only stale locks, writes
artifacts atomically, and does not rewrite unchanged deployment outputs.

Build and verify the deployment bridge:

```bash
python scripts/build_validated_strategy_deployment_v2_19.py
python scripts/audit_validated_strategy_deployment_v2_19.py
```

Run the research-only automation and strict forward-signal gate:

```bash
python scripts/run_validated_strategy_automation_v2_19.py
```

Run the full local finalization, optionally rebuilding v2.18 first:

```bash
python scripts/run_research_automation_finalization_v2_19.py \
  --refresh-v2-18 \
  --limit-symbols 5 \
  --full-tests
```

Deployment outputs are written below
`artifacts/research_runtime/validated_strategy_deployment_v2_19/`. Strict
forward-signal outputs are written below
`artifacts/research_runtime/validated_forward_signal_state_v2_19/`.

## v0.4.3: v2.18 validated-strategy handoff

v2.18 converts the completed v2.17 cross-engine replay into an immutable,
fail-closed research handoff. A strategy is registered only when the configured
scope is exact and Native, PyBroker, NautilusTrader and LEAN all report
`FULL_ENGINE_REPLAY` with parity on the same canonical packet and bar hashes.

The handoff records SHA-256 hashes for the validation configuration, summaries,
audits, canonical schedules, ledgers and parity rows. Any missing engine,
partial replay, blocker, changed hash, missing evidence file, broker call, order
call or non-`NONE` authority rejects the build.

Build and independently verify the handoff from existing v2.17 evidence:

```bash
python scripts/build_cross_engine_handoff_v2_18.py
python scripts/audit_cross_engine_handoff_v2_18.py
```

Run the complete v2.18 gate, optionally refreshing v2.17 first:

```bash
python scripts/run_cross_engine_finalization_v2_18.py --full-tests
python scripts/run_cross_engine_finalization_v2_18.py \
  --refresh-v2-17 \
  --limit-symbols 5 \
  --full-tests
```

Outputs are written below
`artifacts/research_runtime/cross_engine_handoff_v2_18/` and remain
research-only. v2.18 does not grant broker authority or automatic live
promotion.

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

## RL and MARL research pipeline

The v2.21 pipeline is operational and remains shadow-only. It supports a shared
MAPPO actor with a centralized critic and an isolated MATD3 benchmark. Neither
path has a broker interface or execution authority.

Install the research dependencies:

```bash
python -m pip install -e '.[rl,dev]'
```

Download or place canonical Parquet files under `data/derived`,
`data/adjusted`, or `data/processed`, then run one cheap end-to-end check:

```bash
python scripts/run_rl_marl_pipeline_v2_21.py --smoke
```

Run the configured ten-seed walk-forward matrix:

```bash
python scripts/run_rl_marl_pipeline_v2_21.py \
  --config config/rl_marl_pipeline_v2_21.yaml \
  --verify-reproducibility
```

Audit a completed run without retraining:

```bash
python scripts/audit_rl_marl_pipeline_v2_21.py \
  artifacts/rl_marl/v2_21/<config-hash>-<dataset-hash>
```

The pipeline provides:

- aligned point-in-time features without forward-filled bars;
- train-only feature scaling per purged walk-forward fold;
- deterministic seed and fold ledgers;
- pickle-free NumPy checkpoints with SHA-256 manifests;
- untouched OOS evaluation at 1.0x, 1.5x, and 2.0x costs;
- concentration, drawdown, baseline, DSR, and confidence gates;
- fail-closed research decisions with `EXECUTION_AUTHORITY NONE`.

Promotion remains blocked until the full ten-seed evidence passes every gate,
including explicit regime coverage. Passing the research gate still does not
grant live execution authority.

## Strategy generation and diversity lab

v2.22 expands research beyond the two currently cross-engine validated RSI and
OBV strategies. It adds nine separate 1h research families:

- multi-horizon momentum;
- Keltner and volume breakouts;
- Kaufman efficiency-ratio trends;
- Chaikin money-flow confirmation;
- ATR-normalized pullback resumptions;
- range contraction and expansion;
- opening-gap recovery;
- Aroon trend persistence;
- breakout and retest market structure.

Generate the deterministic catalog without market data:

```bash
python scripts/run_strategy_generation_v2_22.py --catalog-only
```

Run the full purged walk-forward research round on the configured nine-symbol
development universe:

```bash
python scripts/run_strategy_research_finalization_v2_22.py --full-tests
```

The runner evaluates train, validation, stressed validation, and untouched test
segments. Candidates must also pass symbol-breadth, trade-concentration,
forced-exit, complexity, family-cap, and redundancy gates. Passing candidates
enter a cross-engine validation queue. They are not finalists and they receive
no broker or live execution authority.

## Tests

v0.4 adds deterministic tests for:

- integration JSON contract round-trips;
- integration registry path resolution;
- subprocess runner protocol and run manifests;
- canonical OHLCV validation;
- split-adjustment continuity;
- canonical Parquet hash round-trip when PyArrow is available;
- existing intelligence/RL/TradeIntent behavior.
