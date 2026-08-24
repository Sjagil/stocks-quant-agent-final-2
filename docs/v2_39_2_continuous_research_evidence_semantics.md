# v2.39.2 Continuous Research Evidence Semantics

v2.39.2 keeps the persistent v2.39 database/job/experiment runtime and the fail-closed v2.39.1 champion gate, but aligns **quality scoring, freshness, evidence breadth and audit reasons with the hard gate**.

## Corrections

1. Cross-engine and generalization remain mandatory foundation gates, but do not double-count as promotion evidence breadth.
2. Freshness for champion review must come from OOS, cost, shadow or calibration evidence; static foundation metadata is insufficient.
3. OOS quality is sample-aware. Positive but zero-sample diagnostics cannot score as perfect OOS evidence.
4. Cost robustness is multiplier-aware. Positive 1x cost evidence cannot score like positive 2x evidence.
5. Validation status and rejected promotion stages have distinct audit labels.
6. Every assessment exposes both `quality_score` and `promotion_readiness_score`.
7. Existing v2.39 and v2.39.1 CLI entrypoints forward to the v2.39.2 runtime after installation.

## Authority

Research only. Broker submission is disabled. Automatic champion/live promotion is disabled. Execution authority remains `NONE`.
