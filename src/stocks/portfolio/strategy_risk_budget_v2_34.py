from __future__ import annotations
import numpy as np
import pandas as pd

def evidence_risk_budgets(expected_returns: pd.Series, *, validation_scores: pd.Series | None=None, stability_scores: pd.Series | None=None, liquidity_scores: pd.Series | None=None, tail_losses: pd.Series | None=None, floor: float=1e-6) -> pd.Series:
    mu=pd.to_numeric(expected_returns,errors="coerce").fillna(0.0).clip(lower=0.0)
    idx=mu.index
    def q(s): return pd.Series(1.0,index=idx) if s is None else pd.to_numeric(s,errors="coerce").reindex(idx).fillna(0.0).clip(0.0,1.0)
    quality=q(validation_scores)*q(stability_scores)*q(liquidity_scores)
    tail=pd.Series(1.0,index=idx) if tail_losses is None else pd.to_numeric(tail_losses,errors="coerce").reindex(idx).abs().replace(0.0,np.nan)
    if tail_losses is None:
        edge=mu
    else:
        fallback=float(tail.dropna().median()) if tail.notna().any() else 1.0
        edge=mu/tail.fillna(fallback).clip(lower=1e-8)
    raw=(edge*quality).clip(lower=0.0)+float(floor)
    return raw/max(float(raw.sum()),1e-18)

def heat_contributions(weights: pd.Series, stop_loss_fractions: pd.Series) -> pd.Series:
    w=pd.to_numeric(weights,errors="coerce").fillna(0.0).clip(lower=0.0)
    s=pd.to_numeric(stop_loss_fractions,errors="coerce").reindex(w.index).fillna(0.0).clip(lower=0.0)
    return w*s

def portfolio_heat(weights: pd.Series, stop_loss_fractions: pd.Series) -> float:
    return float(heat_contributions(weights,stop_loss_fractions).sum())

__all__=["evidence_risk_budgets","heat_contributions","portfolio_heat"]
