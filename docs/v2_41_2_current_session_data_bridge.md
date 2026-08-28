# v2.41.2 Current-Session Production Data Bridge

Production no longer treats EODHD finalized intraday history as a current-session feed.
EODHD remains the historical/finalized backfill source. IBKR/TWS supplies recent RTH
historical bars for current-session production decisions over a read-only connection.

Before any IBKR bar can enter the canonical provider fabric:

- IBKR historical data must contain valid OHLCV with unique UTC timestamps;
- at least 3 exact recent bar timestamps must overlap EODHD finalized history;
- the maximum close-price disagreement over the overlap must be <= 50 bps by default;
- only RTH bars from the most recently opened NYSE session are eligible;
- only bars whose full bar interval has closed (plus the configured close lag) are eligible;
- the final merged canonical file must pass the normal production freshness check;
- any stale symbol makes the top-level refresh fail;
- the IBKR bridge is read-only and broker write-call count must stay zero.

No broker submission, risk, live-canary, Shariah, RL-direct-control, or automatic-promotion
setting is changed by this release.
