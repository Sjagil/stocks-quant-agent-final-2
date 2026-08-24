# v2.39.3.1 Evidence Qualification Hotfix

Insufficient or failed evidence remains auditable, but cannot satisfy promotion
breadth, freshness, OOS-positive, cost-stress-pass, or champion-review semantics.

This fixes the v2.39.3 case where an observation-grade cost-stress row could
contain a positive expectancy while also carrying `passed=false` because the
effective OOS sample was below the required threshold. v2.39.2 previously read
the positive expectancy before respecting the explicit failure state.

After this hotfix:

- failed/insufficient evidence stays in SQLite and artifacts;
- it remains visible in broad diagnostic source/class counts;
- it does not count as promotion-grade class/source breadth;
- it does not satisfy decision freshness;
- it does not produce OOS-positive or cost-stress-pass credit;
- legacy evidence with no explicit qualification field remains backward
  compatible.

Execution authority remains NONE. No broker/order/live promotion behavior is
introduced.
