# v2.31 Alpha Factory / Feature Governance

v2.31 converts technical, cross-sectional, factor, fundamental and news inputs into governed research evidence. It is deliberately upstream of portfolio sizing and execution.

## Core rules

- Closed/PIT information only.
- Backward as-of joins only for external facts.
- No compliance/Shariah filtering in feature research; that remains a later final eligibility gate.
- No feature is promoted because it is popular or confirms another oscillator.
- Promotion evidence includes Rank-IC, ICIR, sign stability, correlation redundancy, VIF, drift and optional horizon decay.
- Highly correlated features are clustered rather than counted as independent votes.
- Regime-specific IC is shrunk toward global IC when sample size is small.
- News uses event-specific half-life decay and duplicate-cluster penalties.
- Fundamentals are computed from values already known at the row's point-in-time.
- Execution authority remains NONE.

## Key formulas

Rank IC is Spearman correlation between a cross-sectional feature and forward return at a decision date. ICIR is mean IC divided by IC standard deviation. Feature half-life fits |IC(h)| approximately to an exponential decay and reports ln(2)/lambda when decay is estimable.

PSI measures reference/current distribution drift. VIF is 1/(1-R^2) from regressing a feature on the others. Regime IC uses empirical-Bayes-style shrinkage: n/(n+k)*IC_regime + k/(n+k)*IC_global.

## What v2.31 does not do

It does not place orders, grant live authority, decide portfolio weights, or apply the final compliance universe. Those remain downstream concerns.
