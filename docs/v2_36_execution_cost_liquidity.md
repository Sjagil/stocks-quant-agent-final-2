# v2.36 Execution / Costs / Liquidity Simulator

v2.36 converts gross research edge into executable net edge. It is research/shadow only.

Core contracts:
- commission, exchange fees, spread, slippage, market impact and FX;
- state-dependent slippage from volatility, participation, urgency and time-of-day;
- square-root market impact from order notional / ADV;
- ADV / POV capacity and liquidity buckets;
- deterministic expected fill plus seeded partial-fill simulations;
- market-versus-limit comparison including non-fill opportunity cost;
- expected and realized implementation shortfall;
- break-even gross edge and hard `NET_EDGE_AFTER_COSTS` gate;
- 1x/1.5x/2x/3x cost stress;
- predicted-vs-observed cost calibration;
- v2.34 rebalance cost projection and post-cost utility gate;
- v2.35.1 gem shortlist execution bridge.

No broker order submission, automatic live promotion or final compliance gate is enabled.
