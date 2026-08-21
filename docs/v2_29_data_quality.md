# v2.29 Data Quality + Provider Health

Research/shadow only. No broker authority.

## Core metrics

- Freshness decay: `exp(-ln(2) * lag / half_life)`
- Coverage: `observed / expected`
- duplicate timestamp ratio
- missing OHLCV ratio
- OHLC integrity violations
- negative volume ratio
- timestamp gap ratio
- robust return outlier ratio
- cross-provider OHLC disagreement in basis points
- volume disagreement
- provider OK / EMPTY / ERROR reliability score

Conflicting OHLC is never averaged. Missing market bars are never forward-filled.
Provenance and disagreements remain explicit.

RTH gap checks support `session_timezone` so overnight/weekend closures are not treated as missing intraday bars.
