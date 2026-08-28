# v2.34 Portfolio Intelligence

Research/shadow-only strategy portfolio construction after v2.33 statistical acceptance.

Pipeline:
`v2.33 accepted strategies -> strategy covariance/shrinkage -> risk overlay -> HRP / robust-edge / convex challengers -> deterministic group/turnover projection -> diagnostics -> portfolio utility -> selected research portfolio -> rebalance/attribution`.

Hard invariants: long-only, no leverage, no broker submission, no automatic live promotion, execution authority NONE. Research compliance is deliberately not applied here.

Portfolio utility ranks feasible challengers using expected return minus variance, Expected Shortfall, turnover, and concentration penalties. Hard constraints are projected outside the utility function and cannot be compensated by a better score.
