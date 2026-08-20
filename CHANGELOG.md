# Changelog

## 0.4.4

- Add a v2.19 fail-closed deployment bridge between the immutable v2.18
  cross-engine handoff and the forward-signal engine.
- Freeze and hash the exact strategy parameter payload used by each deployed
  research signal adapter.
- Require exact RSI and OBV deployment coverage, finalist status, source
  fingerprints and zero execution authority before any forward signal can be
  marked ready.
- Add deterministic, atomic and idempotent deployment outputs with stale-lock
  recovery and overlap rejection.
- Add one-command build, audit, signal and finalization runners plus a weekday
  GitHub Actions contract schedule.
- Preserve zero broker calls, zero order calls, no automatic live promotion and
  `execution_authority = NONE` throughout the automation layer.

## 0.4.3

- Add the v2.18 fail-closed handoff for strategies validated by Native,
  PyBroker, NautilusTrader and LEAN full-engine replay.
- Require exact configured strategy and engine coverage, full parity, shared
  canonical packet/bar hashes, frozen parameters and whole-share replay.
- Hash every source configuration, summary, audit, schedule, ledger and parity
  file into an independently verifiable evidence manifest.
- Add a standalone builder, verifier and finalization runner for v2.18.
- Add a focused GitHub Actions gate for the v2.18 contract and failure cases.
- Remove accidentally committed local finalization logs and ignore future
  generated v2 logs.
- Preserve zero broker calls, zero order calls, no automatic live promotion and
  `execution_authority = NONE` throughout the handoff.

## 0.4.2

- Treat FinRL `finnhub` as a truly optional data-source dependency; missing Finnhub no longer downgrades an otherwise healthy FinRL runtime.
- Add MoonDev compatibility with the maintained `pandas-ta-classic` package without modifying the upstream MoonDev reference checkout.
- Keep MoonDev health `OK` when only optional TA helpers are unavailable; warnings remain explicit.
- Make Nautilus catalog probing graceful when the runtime package is absent instead of raising an import error.
- Add a macOS integration-runtime bootstrap script which installs MoonDev TA compatibility and forces NautilusTrader binary-wheel installation from the official Nautech package index, with a known macOS ARM64 CPython 3.12 fallback version.
- Update the extra-agent setup helper to install `pandas-ta-classic` instead of relying on the unavailable legacy `pandas-ta` pin.


## 0.4.1

- Fix isolated integration interpreter routing on macOS/Linux: virtualenv `bin/python` symlinks are now preserved instead of dereferenced to the pyenv/base interpreter.
- Add regression coverage proving isolated Python paths remain inside `.venvs/*`.
- Worker health output now reports `sys.prefix`, `sys.base_prefix`, and whether the virtualenv is active.

## 0.4.0 — integration and canonical-data foundation

### Added

- Versioned JSON worker contracts and typed integration specs.
- YAML registry with environment/path overrides, `.env` support, Git provenance and config hashing.
- Hardened subprocess runner with restricted environment forwarding, action allow-lists, secret-bearing payload rejection, timeout handling, artifact sandbox validation and per-run manifests/logs.
- Isolated workers for VeighNa, Qlib, FinRL-Trading, MoonDev and NautilusTrader.
- VeighNa `alpha158` action with explicit VWAP proxy policy and label opt-in/leakage warning.
- Canonical UTC OHLCV schema, quality reporting, split-adjustment model, sidecar metadata and SHA-256 provenance.
- EODHD intraday/daily downloader wired to canonical data.
- EODHD split normalizer wired to canonical data with double-adjustment protection.
- Integration and canonical-data test coverage.

### Changed

- `validate_rl_data.py` now validates the canonical data contract before feature checks.
- PyYAML and PyArrow are base dependencies.
- `vnpy_ib` is reference-only in the setup helper to avoid forcing the earlier protobuf pin conflict into the VeighNa research environment.

### Safety

- External workers remain research-only and never create broker orders.
- MoonDev trading-agent execution is not exposed by the worker contract.
- Secrets must be passed via allow-listed environment variables, not persisted in JSON worker payloads.
