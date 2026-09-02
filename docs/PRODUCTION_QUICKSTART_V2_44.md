# Production Quickstart v2.44

This is the supported fast path for macOS. It installs the production environment, installs the isolated `Stocks` reference runtime, creates a local `.env`, initializes the state database and runs the first doctor check.

```bash
git switch feature/production-hardening-v2-43-1
bash scripts/bootstrap_production_v2_44.sh
```

Fill `.env` with the EODHD key and IBKR paper account settings. Keep `IBKR_ENVIRONMENT=PAPER` and use TWS paper port `7497` unless the local TWS configuration uses a different paper port.

## Mandatory verification order

```bash
.venv/bin/python scripts/run_production_runtime_v2_41.py doctor
.venv/bin/python scripts/run_production_runtime_v2_41.py screener
.venv/bin/python scripts/run_production_runtime_v2_41.py refresh-data
.venv/bin/python scripts/run_production_runtime_v2_41.py preflight
.venv/bin/python scripts/run_production_hardening_validation_v2_43_1.py
```

The daily screener uses three EODHD universe lanes: core, liquid small/mid-cap gems and tactical movers. It produces at most 150 ranked candidates. It cannot assign a strategy or create an order. A new paper entry is blocked unless its symbol is present in a fresh screener result, the strategy is independently validated, Shariah verification is current, context and risk gates pass, and explicit PAPER submission authority has been enabled.

## Start in observe mode

```bash
.venv/bin/python scripts/run_production_runtime_v2_41.py set-mode OBSERVE
.venv/bin/python scripts/run_production_runtime_v2_41.py cycle --force-data-refresh --force-decision-refresh
.venv/bin/python scripts/run_production_runtime_v2_41.py status
```

## Enable paper submission only after validation is green

```bash
.venv/bin/python scripts/run_production_runtime_v2_41.py set-mode PAPER
.venv/bin/python scripts/run_production_runtime_v2_41.py adopt-baseline
.venv/bin/python scripts/run_production_runtime_v2_41.py enable-submission --environment PAPER
.venv/bin/python scripts/run_production_runtime_v2_41.py watch --interval-seconds 300
```

Do not enable submission when `doctor`, `preflight`, the hardening validation, reconciliation or screener freshness is red. The runtime fails closed and does not enable live submission automatically.
