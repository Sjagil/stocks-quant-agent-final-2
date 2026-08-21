# v2.28 Canonical Quant Math + Portfolio Intelligence

Status: research/shadow only. This package never grants execution authority.

## Purpose

v2.28 replaces ad-hoc duplicate math with canonical primitives shared by research,
portfolio construction and RL. It does not replace the v2.20 deterministic
constraint projector and does not submit broker orders.

## Canonical objective

For research portfolio weights `w`:

`U(w) = w' mu_net - lambda_v w' Sigma w - lambda_es ES - lambda_dd DD
        - lambda_to Turnover - lambda_i Impact - lambda_c Concentration`

Cash is a valid residual allocation.

## Added

- simple/log/forward returns and compounding
- EWMA and range-based volatility
- drawdown, ulcer and pain metrics
- historical VaR / Expected Shortfall / downside risk
- sample, EWMA, Ledoit-Wolf and OAS covariance
- marginal and total risk contribution
- diversification and effective-N metrics
- stop/risk/volatility sizing
- liquidity, Amihud, POV, square-root impact and implementation shortfall
- factor beta and residual returns
- binary/continuous/multi-asset fractional Kelly research primitives
- Sharpe, Sortino, Calmar, IR, profit factor, expectancy and turnover
- PSR and minimum track-record length
- forward-return labels with explicit t+h availability
- IC, Rank-IC, IC decay and feature redundancy
- uncertainty-adjusted forward distributions
- min-variance, Mean-CVaR and risk-budgeting portfolio challengers

## Safety invariants

- `execution_authority = NONE`
- no broker imports in v2.28 quant or optimizer modules
- no order submission
- no automatic live promotion
- forward labels are research labels only and unavailable for the final `h` rows
- production hard constraints remain downstream in the deterministic projector
