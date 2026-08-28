from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from .feature_governance_v2_31 import estimate_ic_half_life
from .feature_ic_v2_28 import cross_sectional_ic_series, summarize_ic


def cross_sectional_ic_decay_curve(
    panel: pd.DataFrame,
    *,
    feature_id: str,
    date_column: str,
    forward_targets: Mapping[int, str],
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for horizon, target in sorted((int(h), str(c)) for h, c in forward_targets.items()):
        if target not in panel.columns:
            raise ValueError(f"forward target missing: {target}")
        ic = cross_sectional_ic_series(
            panel,
            date_column=date_column,
            feature_column=feature_id,
            target_column=target,
            rank=True,
        )
        summary = summarize_ic(ic)
        rows.append(
            {
                "feature_id": feature_id,
                "horizon_bars": horizon,
                "mean_rank_ic": float(summary.mean_ic),
                "rank_icir": float(summary.icir),
                "periods": int(summary.periods),
            }
        )
    out = pd.DataFrame(rows)
    return out


def decay_half_life_from_curve(curve: pd.DataFrame) -> float | None:
    required = {"horizon_bars", "mean_rank_ic"}
    if missing := required.difference(curve.columns):
        raise ValueError(f"curve missing columns: {sorted(missing)}")
    mapping = {
        float(row.horizon_bars): float(row.mean_rank_ic)
        for row in curve.itertuples(index=False)
        if np.isfinite(row.mean_rank_ic)
    }
    return estimate_ic_half_life(mapping)


__all__ = ["cross_sectional_ic_decay_curve", "decay_half_life_from_curve"]
