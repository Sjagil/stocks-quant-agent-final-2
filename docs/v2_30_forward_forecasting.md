# v2.30 Forward Forecasting Foundation

Research/shadow only.

This layer is the intended replacement path for heuristic score-to-return mappings.
It provides:

- chronological purged walk-forward splits
- explicit label-horizon overlap assertions
- mean and q10/q50/q90 return forecasts
- deterministic quantile no-crossing projection
- Brier, ECE, pinball and quantile coverage metrics
- OOS-only walk-forward forecast artifacts
- uncertainty/downside/cost-aware opportunity scoring

No random train/test shuffling is used in the walk-forward contract.
No broker authority is granted.
