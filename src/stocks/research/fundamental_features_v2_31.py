from __future__ import annotations

import numpy as np
import pandas as pd

from stocks.quant.normalization import robust_zscore


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0.0, np.nan)


def build_fundamental_raw_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build PIT fundamental ratios from values already known at each row's as-of time.

    This function never fetches data and never shifts future filings backwards. The caller
    is responsible for supplying point-in-time source rows.
    """
    out = pd.DataFrame(index=frame.index)
    nopat = _num(frame, "nopat")
    invested_capital = _num(frame, "invested_capital")
    fcf = _num(frame, "free_cash_flow")
    revenue = _num(frame, "revenue")
    gross_profit = _num(frame, "gross_profit")
    net_income = _num(frame, "net_income")
    avg_assets = _num(frame, "average_assets")
    market_cap = _num(frame, "market_cap")
    ebitda = _num(frame, "ebitda")
    net_debt = _num(frame, "net_debt")
    ebit = _num(frame, "ebit")
    interest_expense = _num(frame, "interest_expense").abs()
    actual_eps = _num(frame, "actual_eps")
    consensus_eps = _num(frame, "consensus_eps")
    eps_estimate = _num(frame, "eps_estimate")
    eps_estimate_prior = _num(frame, "eps_estimate_prior")
    revenue_prior = _num(frame, "revenue_prior")
    eps = _num(frame, "eps")
    eps_prior = _num(frame, "eps_prior")
    fcf_prior = _num(frame, "free_cash_flow_prior")
    gross_margin_prior = _num(frame, "gross_margin_prior")

    out["roic"] = _safe_div(nopat, invested_capital)
    out["fcf_margin"] = _safe_div(fcf, revenue)
    out["gross_margin"] = _safe_div(gross_profit, revenue)
    out["accrual_ratio"] = _safe_div(net_income - fcf, avg_assets)
    out["fcf_yield"] = _safe_div(fcf, market_cap)
    out["earnings_yield"] = _safe_div(net_income, market_cap)
    out["net_debt_to_ebitda"] = _safe_div(net_debt, ebitda)
    out["interest_coverage"] = _safe_div(ebit, interest_expense)
    out["revenue_growth"] = _safe_div(revenue, revenue_prior) - 1.0
    out["eps_growth"] = _safe_div(eps - eps_prior, eps_prior.abs())
    out["fcf_growth"] = _safe_div(fcf - fcf_prior, fcf_prior.abs())
    out["margin_expansion"] = out["gross_margin"] - gross_margin_prior
    out["earnings_surprise"] = _safe_div(actual_eps - consensus_eps, consensus_eps.abs())
    out["eps_revision"] = _safe_div(eps_estimate - eps_estimate_prior, eps_estimate_prior.abs())
    return out.replace([np.inf, -np.inf], np.nan)


def _cross_sectional_z(
    frame: pd.DataFrame,
    *,
    date_column: str,
    value: pd.Series,
    clip: float = 3.0,
) -> pd.Series:
    work = pd.DataFrame({date_column: frame[date_column], "value": value}, index=frame.index)
    return work.groupby(date_column, sort=False)["value"].transform(lambda s: robust_zscore(s, clip=clip))


def score_fundamental_panel(
    frame: pd.DataFrame,
    *,
    date_column: str,
) -> pd.DataFrame:
    """Return raw PIT ratios plus quality/growth/revision/value composites.

    Composites use cross-sectional robust z-scores so assets with different scales are
    comparable. Missing inputs remain missing and are excluded from each row's weighted
    average rather than silently imputed from future data.
    """
    if date_column not in frame.columns:
        raise ValueError("date_column is required")
    raw = build_fundamental_raw_features(frame)
    z = pd.DataFrame(index=frame.index)
    for column in raw.columns:
        z[column] = _cross_sectional_z(frame, date_column=date_column, value=raw[column])

    def weighted(columns: dict[str, float]) -> pd.Series:
        numerator = pd.Series(0.0, index=frame.index, dtype=float)
        denominator = pd.Series(0.0, index=frame.index, dtype=float)
        for column, weight in columns.items():
            values = z[column]
            available = values.notna().astype(float)
            numerator = numerator + values.fillna(0.0) * float(weight)
            denominator = denominator + available * abs(float(weight))
        return numerator / denominator.replace(0.0, np.nan)

    quality = weighted(
        {
            "roic": 0.24,
            "fcf_margin": 0.20,
            "gross_margin": 0.14,
            "accrual_ratio": -0.16,
            "net_debt_to_ebitda": -0.12,
            "interest_coverage": 0.14,
        }
    )
    growth = weighted(
        {
            "revenue_growth": 0.30,
            "eps_growth": 0.30,
            "fcf_growth": 0.20,
            "margin_expansion": 0.20,
        }
    )
    revisions = weighted({"eps_revision": 0.55, "earnings_surprise": 0.45})
    value = weighted({"fcf_yield": 0.60, "earnings_yield": 0.40})
    combined = pd.concat(
        [
            quality.rename("quality"),
            growth.rename("growth"),
            revisions.rename("revisions"),
            value.rename("value"),
        ],
        axis=1,
    )
    weights = pd.Series({"quality": 0.30, "growth": 0.25, "revisions": 0.30, "value": 0.15})
    numerator = combined.mul(weights, axis=1).sum(axis=1, skipna=True)
    denominator = combined.notna().mul(weights.abs(), axis=1).sum(axis=1)
    score = numerator / denominator.replace(0.0, np.nan)

    result = pd.concat([raw.add_prefix("fund_raw_"), z.add_prefix("fund_z_")], axis=1)
    result["fundamental_quality_score"] = quality
    result["fundamental_growth_score"] = growth
    result["fundamental_revision_score"] = revisions
    result["fundamental_value_score"] = value
    result["fundamental_composite_score"] = score
    return result


__all__ = ["build_fundamental_raw_features", "score_fundamental_panel"]
