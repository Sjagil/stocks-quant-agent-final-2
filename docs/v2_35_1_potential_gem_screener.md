# v2.35.1 Potential Gem Screener

The screener ranks common stocks for research attention. It is not an order generator and not a promise of future returns.

## Core design
- hard investability/data-quality filters before ranking;
- sector-relative percentile transforms to avoid raw-metric comparability errors;
- quality, growth, revisions, value, momentum, forward forecast and catalyst evidence;
- weighted geometric aggregation so one extreme feature cannot dominate every weak dimension;
- forecast asymmetry using q10/q90 and expected costs;
- liquidity/data-quality/portfolio-fit multipliers;
- explicit risk penalty for volatility, drawdown, spread, leverage, dilution and pump-like return/volume behavior;
- hard pump/manipulation-risk blocker when an extreme move has extreme volume but weak independent news-source diversity;
- sector/industry diversity caps in the final shortlist.

Shariah/compliance is intentionally not applied as a research gate here; final compliance remains downstream. Execution authority is NONE.
