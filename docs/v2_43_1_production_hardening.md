# v2.43.1 Production Hardening

This round fixes the blockers observed after v2.43 without weakening any safety gate.

## Imported Stocks repo used as a real donor

`references/Stocks` is used through the existing isolated integrations for:

- native IBKR historical data and callback semantics;
- read-only broker reconciliation and double-snapshot stability;
- read-only realtime quote semantics;
- PIT macro context and provider provenance;
- architectural reference for bounded PAPER execution. PAPER submission is not enabled by this installer.

## Main changes

1. IBKR historical calls are chunked at two symbols, with failed-symbol retries and per-chunk diagnostics.
2. Historical market-data settings are decoupled from reconciliation secrets/client IDs.
3. Read-only broker preflight uses the imported Stocks reconciliation path instead of `ib_async` startup synchronization.
4. EODHD economic calendar loads project `.env`, falls back to Finnhub, caches bounded results and records provider diagnostics.
5. Imported Stocks macro context is added to the immutable market context snapshot as context-only evidence.
6. FinancialNLP/FinBERT is process-singleton within snapshot construction instead of being re-created per symbol.
7. Strategy hydration writes an explicit freshness marker. Forward signals fail closed for new exposure when hydration is stale or failed.
8. Context readiness is split into `system_paper_ready` and `entry_eligible_now`.
9. Context walk-forward can use historical causal replay instead of waiting for weeks of live snapshots.
10. Existing cross-provider 50 bps price disagreement limit is unchanged. PPO remains weight 0. SAC remains shadow-only. RL broker control remains false.

## PAPER rule

The installer does not arm or enable order submission. Even when `system_paper_ready=true`, an order still requires a current genuine fresh strategy trigger, Shariah verification, context approval, risk approval, broker readiness, idempotency and the existing explicit submission authority.

## v2.44 deployability completion

The executable deployment path is `scripts/bootstrap_production_v2_44.sh`. It supplies the missing environment template, production dependency set and isolated `references/Stocks` runtime. The native EODHD screener now runs inside the decision refresh chain every six hours and blocks new entries when its artifact is missing, stale, invalid or does not contain the proposed symbol. The screener remains advisory and cannot assign strategies or submit orders.
