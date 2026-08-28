# v2.35 Stocks + ETF + Commodity Exposure Engine

v2.35 sits after portfolio intelligence. It expands portfolio diagnostics from strategy weights to instrument and economic exposures.

Core contracts:
- STOCK, ETF, COMMODITY and COMMODITY_ETF asset kinds.
- Point-in-time ETF holdings: only snapshots with `available_at <= decision_time`.
- ETF look-through into sector, industry, country, currency, factor and commodity exposures.
- Weighted ETF overlap and concentration diagnostics.
- Factor beta estimation and portfolio factor aggregation.
- Commodity curve, roll-yield/backwardation, inventory and macro-regime diagnostics.
- Hard research blockers for concentration and unknown look-through exposure.

This layer is research/shadow only. It does not apply the final compliance gate and cannot submit broker orders.
