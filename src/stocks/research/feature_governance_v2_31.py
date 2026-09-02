from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .feature_ic_v2_28 import cross_sectional_ic_series, summarize_ic


@dataclass(frozen=True)
class FeatureGovernancePolicy:
    min_ic_periods: int = 8
    min_abs_mean_rank_ic: float = 0.01
    min_abs_icir: float = 0.10
    min_sign_consistency: float = 0.55
    max_redundancy: float = 0.95
    max_vif: float = 20.0
    max_psi: float = 0.25
    min_stability_score: float = 0.20

    def __post_init__(self) -> None:
        if self.min_ic_periods < 3:
            raise ValueError("min_ic_periods must be >= 3")
        if self.min_abs_mean_rank_ic < 0 or self.min_abs_icir < 0:
            raise ValueError("IC thresholds cannot be negative")
        if not 0.5 <= self.min_sign_consistency <= 1.0:
            raise ValueError("min_sign_consistency must be in [0.5,1]")
        if not 0.0 <= self.max_redundancy <= 1.0:
            raise ValueError("max_redundancy must be in [0,1]")
        if self.max_vif <= 1.0 or self.max_psi < 0:
            raise ValueError("invalid VIF/PSI thresholds")
        if not 0.0 <= self.min_stability_score <= 1.0:
            raise ValueError("min_stability_score must be in [0,1]")


@dataclass(frozen=True)
class FeatureGovernanceResult:
    feature_id: str
    status: str
    blockers: tuple[str, ...]
    mean_rank_ic: float
    rank_ic_std: float
    rank_icir: float
    sign_consistency: float
    ic_periods: int
    decay_half_life: float | None
    redundancy: float
    vif: float | None
    psi: float | None
    stability_score: float
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def variance_inflation_factors(features: pd.DataFrame) -> pd.Series:
    numeric = features.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    complete = numeric.dropna()
    result: dict[str, float] = {column: float("nan") for column in numeric.columns}
    if len(complete) < max(5, numeric.shape[1] + 2):
        return pd.Series(result, dtype=float)
    for target in numeric.columns:
        others = [column for column in numeric.columns if column != target]
        if not others:
            result[target] = 1.0
            continue
        y = complete[target].to_numpy(dtype=float)
        x = complete[others].to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        fitted = x @ coef
        sst = float(np.dot(y - y.mean(), y - y.mean()))
        sse = float(np.dot(y - fitted, y - fitted))
        if sst <= 1e-18:
            result[target] = float("inf")
            continue
        r2 = float(np.clip(1.0 - sse / sst, 0.0, 1.0))
        result[target] = float("inf") if r2 >= 1.0 - 1e-12 else float(1.0 / (1.0 - r2))
    return pd.Series(result, dtype=float)


def redundancy_matrix(features: pd.DataFrame, *, method: str = "spearman") -> pd.DataFrame:
    if method not in {"pearson", "spearman", "kendall"}:
        raise ValueError("unsupported correlation method")
    return features.apply(pd.to_numeric, errors="coerce").corr(method=method).abs()


def correlation_clusters(
    features: pd.DataFrame,
    *,
    threshold: float = 0.90,
    method: str = "spearman",
) -> tuple[tuple[str, ...], ...]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0,1]")
    corr = redundancy_matrix(features, method=method)
    nodes = list(corr.columns)
    visited: set[str] = set()
    clusters: list[tuple[str, ...]] = []
    for node in nodes:
        if node in visited:
            continue
        stack = [node]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            visited.add(current)
            neighbors = [
                other
                for other in nodes
                if other != current
                and np.isfinite(corr.loc[current, other])
                and float(corr.loc[current, other]) >= threshold
            ]
            stack.extend(neighbors)
        clusters.append(tuple(sorted(component)))
    return tuple(sorted(clusters, key=lambda values: (values[0], len(values))))


def estimate_ic_half_life(ic_by_horizon: dict[float, float]) -> float | None:
    """Fit |IC(h)| ~= a exp(-lambda h); return ln(2)/lambda when decay exists."""
    points = sorted(
        (float(h), abs(float(ic)))
        for h, ic in ic_by_horizon.items()
        if float(h) > 0 and np.isfinite(ic) and abs(float(ic)) > 1e-12
    )
    if len(points) < 2:
        return None
    x = np.asarray([p[0] for p in points], dtype=float)
    y = np.log(np.asarray([p[1] for p in points], dtype=float))
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    decay = -float(coef[1])
    if not np.isfinite(decay) or decay <= 1e-12:
        return None
    return float(math.log(2.0) / decay)


def feature_stability_score(ic_series: pd.Series) -> float:
    values = pd.to_numeric(ic_series, errors="coerce").dropna().astype(float)
    if len(values) < 3:
        return 0.0
    magnitude = abs(float(values.mean()))
    dispersion = float(values.std(ddof=1))
    sign_consistency = max(float((values > 0).mean()), float((values < 0).mean()))
    signal_to_noise = magnitude / (magnitude + dispersion + 1e-12)
    return float(np.clip(0.5 * signal_to_noise + 0.5 * sign_consistency, 0.0, 1.0))


def max_feature_redundancy(features: pd.DataFrame, feature_id: str) -> float:
    corr = redundancy_matrix(features)
    if feature_id not in corr.columns:
        return float("nan")
    others = corr[feature_id].drop(index=feature_id, errors="ignore").dropna()
    return 0.0 if others.empty else float(others.max())


def evaluate_feature_governance(
    panel: pd.DataFrame,
    *,
    feature_id: str,
    date_column: str,
    target_column: str,
    all_features: pd.DataFrame | None = None,
    ic_decay: dict[float, float] | None = None,
    psi: float | None = None,
    policy: FeatureGovernancePolicy | None = None,
) -> FeatureGovernanceResult:
    cfg = policy or FeatureGovernancePolicy()
    ic = cross_sectional_ic_series(
        panel,
        date_column=date_column,
        feature_column=feature_id,
        target_column=target_column,
        rank=True,
    ).dropna()
    summary = summarize_ic(ic)
    sign_consistency = (
        max(float((ic > 0).mean()), float((ic < 0).mean())) if len(ic) else 0.0
    )
    stability = feature_stability_score(ic)
    redundancy = (
        max_feature_redundancy(all_features, feature_id)
        if all_features is not None and feature_id in all_features.columns
        else 0.0
    )
    vif_value: float | None = None
    if all_features is not None and feature_id in all_features.columns:
        value = variance_inflation_factors(all_features).get(feature_id, np.nan)
        vif_value = float(value) if np.isfinite(value) else None
    half_life = estimate_ic_half_life(ic_decay or {})

    blockers: list[str] = []
    if summary.periods < cfg.min_ic_periods:
        blockers.append("INSUFFICIENT_IC_PERIODS")
    if not np.isfinite(summary.mean_ic) or abs(summary.mean_ic) < cfg.min_abs_mean_rank_ic:
        blockers.append("RANK_IC_TOO_WEAK")
    if not np.isfinite(summary.icir) or abs(summary.icir) < cfg.min_abs_icir:
        blockers.append("ICIR_TOO_WEAK")
    if sign_consistency < cfg.min_sign_consistency:
        blockers.append("IC_SIGN_UNSTABLE")
    if np.isfinite(redundancy) and redundancy > cfg.max_redundancy:
        blockers.append("FEATURE_REDUNDANT")
    if vif_value is not None and vif_value > cfg.max_vif:
        blockers.append("MULTICOLLINEARITY_HIGH")
    if psi is not None and np.isfinite(psi) and psi > cfg.max_psi:
        blockers.append("DISTRIBUTION_DRIFT_HIGH")
    if stability < cfg.min_stability_score:
        blockers.append("FEATURE_STABILITY_LOW")

    return FeatureGovernanceResult(
        feature_id=feature_id,
        status="PROMOTE_RESEARCH" if not blockers else "REJECT_OR_REVIEW",
        blockers=tuple(blockers),
        mean_rank_ic=float(summary.mean_ic),
        rank_ic_std=float(summary.std_ic),
        rank_icir=float(summary.icir),
        sign_consistency=float(sign_consistency),
        ic_periods=int(summary.periods),
        decay_half_life=half_life,
        redundancy=float(redundancy),
        vif=vif_value,
        psi=None if psi is None else float(psi),
        stability_score=float(stability),
    )


__all__ = [
    "FeatureGovernancePolicy",
    "FeatureGovernanceResult",
    "correlation_clusters",
    "estimate_ic_half_life",
    "evaluate_feature_governance",
    "feature_stability_score",
    "redundancy_matrix",
    "variance_inflation_factors",
]
