# v2.41 Production Runtime

v2.41 separates broker authority from research and RL learning. It automates closed-bar EODHD refresh, forward decisions, read-only broker observation, fill ingestion, reconciliation, risk sizing, protected whole-share orders, persistent idempotency, daily drawdown kill, and macOS launchd supervision.

## Modes

- `OBSERVE`: data/decision/broker preflight only; no writes.
- `PAPER`: automated IBKR paper orders only after explicit `enable-submission --environment PAPER`.
- `LIVE_CANARY`: real account writes require all preflight gates, an explicit expiring `arm-live`, explicit LIVE submission enablement, an EUR-base account, and a configured positive live-canary notional cap.

Automatic live promotion remains disabled. RL policies cannot directly control broker orders in v2.41. The broker runtime consumes deterministic portfolio proposals that already require fresh closed-bar triggers and Shariah verification.

## First deployment

1. `doctor`
2. `init`
3. `refresh-data`
4. start TWS/IB Gateway and set `IBKR_ENVIRONMENT=PAPER`
5. `adopt-baseline`
6. `set-mode PAPER`
7. `preflight`
8. `enable-submission --environment PAPER`
9. `cycle --force-data-refresh --force-decision-refresh`
10. after observing paper behavior, `install-launchd --interval-seconds 300`

Live canary is deliberately not enabled by installation.

## Additional fail-closed invariants

- Any data-refresh or decision-refresh error blocks broker writes for that cycle.
- A second complete preflight is evaluated on a fresh broker snapshot immediately before writes.
- Read-only preflight must report zero broker write calls.
- Broker/server clock drift must remain within the configured tolerance.
- If protective-stop staging fails, the non-transmitting parent entry is explicitly cancelled.
