from __future__ import annotations

import numpy as np
import pandas as pd


def _numeric(values: pd.Series) -> np.ndarray:
    return pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    if bins < 2:
        raise ValueError("bins must be >= 2")
    ref = _numeric(reference)
    cur = _numeric(current)
    if len(ref) < bins or len(cur) < 2:
        return float("nan")
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.unique(np.quantile(ref, quantiles))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)
    p = ref_counts.astype(float) / max(len(ref), 1)
    q = cur_counts.astype(float) / max(len(cur), 1)
    p = np.clip(p, epsilon, None)
    q = np.clip(q, epsilon, None)
    p /= p.sum()
    q /= q.sum()
    return float(np.sum((p - q) * np.log(p / q)))


def jensen_shannon_divergence(
    reference: pd.Series,
    current: pd.Series,
    *,
    bins: int = 20,
    epsilon: float = 1e-12,
) -> float:
    ref = _numeric(reference)
    cur = _numeric(current)
    if len(ref) < 2 or len(cur) < 2:
        return float("nan")
    low = min(float(np.min(ref)), float(np.min(cur)))
    high = max(float(np.max(ref)), float(np.max(cur)))
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return 0.0
    edges = np.linspace(low, high, bins + 1)
    p, _ = np.histogram(ref, bins=edges)
    q, _ = np.histogram(cur, bins=edges)
    p = np.clip(p.astype(float), epsilon, None)
    q = np.clip(q.astype(float), epsilon, None)
    p /= p.sum()
    q /= q.sum()
    m = 0.5 * (p + q)
    kl_pm = float(np.sum(p * np.log(p / m)))
    kl_qm = float(np.sum(q * np.log(q / m)))
    return 0.5 * (kl_pm + kl_qm)


def drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    *,
    features: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    columns = list(features) if features is not None else sorted(set(reference.columns).intersection(current.columns))
    rows: list[dict[str, float | str]] = []
    for feature in columns:
        if feature not in reference.columns or feature not in current.columns:
            continue
        psi = population_stability_index(reference[feature], current[feature])
        js = jensen_shannon_divergence(reference[feature], current[feature])
        rows.append({"feature_id": feature, "psi": psi, "js_divergence": js})
    return pd.DataFrame(rows)


__all__ = ["drift_report", "jensen_shannon_divergence", "population_stability_index"]
