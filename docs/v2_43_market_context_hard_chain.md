# v2.43 Market Context Hard Chain

v2.43 makes context a causal production dependency instead of an optional overlay.

## Chain

1. EODHD finalized history plus read-only IBKR current-session hydration.
2. Immutable content-addressed `MarketContextSnapshot` at one decision cutoff.
3. Economic calendar visibility gate.
4. Multi-provider news ingestion, duplicate clustering and finance NLP.
5. Forward signal engine.
6. Portfolio decision.
7. Context policy using the exact same snapshot.
8. Context readiness gate.
9. PAPER stays blocked until every readiness check passes.

## Invariants

- No future or unverified economic actual/revision/surprise.
- High-impact events block new exposure 30 minutes before release.
- After release, wait for release data and a relevant closed bar.
- Missing calendar context blocks new entries.
- Missing critical single-stock news context blocks new entries.
- Duplicate news is clustered before weighting.
- Context can reduce/block an entry but cannot create one.
- Existing-position/risk-reducing paths remain available.
- PPO weight is 0.
- SAC is SHADOW_CONTEXT_ONLY.
- RL direct broker control is false.
- New entries never fall back to raw proposals when context is stale/missing.
