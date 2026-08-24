# v2.37 Full Shadow Portfolio Lifecycle

v2.37 turns the stateless research and execution-cost layers into a persistent,
replayable shadow portfolio lifecycle.

Lifecycle:

`DECISION -> EDGE/CAPACITY GATE -> SHADOW ORDER -> PARTIAL/FULL FILL -> POSITION
-> MARK/MFE/MAE -> EXIT SIGNAL -> SHADOW EXIT FILL -> CLOSED TRADE
-> ATTRIBUTION -> FORECAST/COST FEEDBACK`

Core invariants:
- append-only SQLite event ledger with hash-chain integrity;
- deterministic idempotency key from strategy, symbol, decision time, side and intent;
- restart-safe replay: the same events reconstruct the same order/position state;
- v2.36 executable-edge gate is mandatory for new entries;
- risk exits use v2.36 costs/liquidity but are not blocked by a positive-alpha requirement;
- long-only: exits cannot create negative positions;
- reconciliation is fail-closed;
- realized costs, MFE/MAE, holding period, exit reason and forecast/cost error are persisted;
- no broker order submission or live authority.
