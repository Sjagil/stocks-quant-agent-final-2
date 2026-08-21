from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .drift_v2_31 import population_stability_index
from .feature_decay_v2_31 import cross_sectional_ic_decay_curve, decay_half_life_from_curve
from .feature_governance_v2_31 import (
    FeatureGovernancePolicy,
    correlation_clusters,
    evaluate_feature_governance,
    variance_inflation_factors,
)
from .feature_registry_v2_31 import FeatureRegistry, default_feature_registry


@dataclass(frozen=True)
class AlphaFactoryV231Result:
    status: str
    feature_count: int
    promoted_count: int
    rejected_count: int
    governance: tuple[dict[str, object], ...]
    clusters: tuple[tuple[str, ...], ...]
    vif: dict[str, float | None]
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class AlphaFactoryV231:
    """Canonical feature governance over forward outcomes.

    This class evaluates evidence only. It does not size positions, place orders, grant
    live authority, or apply compliance eligibility.
    """

    def __init__(
        self,
        *,
        registry: FeatureRegistry | None = None,
        policy: FeatureGovernancePolicy | None = None,
    ) -> None:
        self.registry = registry or default_feature_registry()
        self.policy = policy or FeatureGovernancePolicy()

    def evaluate(
        self,
        panel: pd.DataFrame,
        *,
        feature_ids: Sequence[str],
        date_column: str,
        primary_target: str,
        forward_targets: Mapping[int, str] | None = None,
        reference_mask: pd.Series | None = None,
        current_mask: pd.Series | None = None,
    ) -> AlphaFactoryV231Result:
        feature_ids = tuple(dict.fromkeys(str(x) for x in feature_ids))
        for feature_id in feature_ids:
            self.registry.get(feature_id)
            if feature_id not in panel.columns:
                raise ValueError(f"feature missing from panel: {feature_id}")
        if date_column not in panel.columns or primary_target not in panel.columns:
            raise ValueError("date/target column missing")
        feature_frame = panel.loc[:, feature_ids].apply(pd.to_numeric, errors="coerce")
        clusters = correlation_clusters(feature_frame, threshold=self.policy.max_redundancy)
        vif_series = variance_inflation_factors(feature_frame)
        governance: list[dict[str, object]] = []

        for feature_id in feature_ids:
            psi: float | None = None
            if reference_mask is not None and current_mask is not None:
                psi_value = population_stability_index(
                    panel.loc[reference_mask, feature_id],
                    panel.loc[current_mask, feature_id],
                )
                psi = float(psi_value) if np.isfinite(psi_value) else None
            decay_mapping: dict[float, float] = {}
            decay_half_life: float | None = None
            if forward_targets:
                curve = cross_sectional_ic_decay_curve(
                    panel,
                    feature_id=feature_id,
                    date_column=date_column,
                    forward_targets=forward_targets,
                )
                decay_mapping = {
                    float(row.horizon_bars): float(row.mean_rank_ic)
                    for row in curve.itertuples(index=False)
                    if np.isfinite(row.mean_rank_ic)
                }
                decay_half_life = decay_half_life_from_curve(curve)
            result = evaluate_feature_governance(
                panel,
                feature_id=feature_id,
                date_column=date_column,
                target_column=primary_target,
                all_features=feature_frame,
                ic_decay=decay_mapping,
                psi=psi,
                policy=self.policy,
            )
            payload = result.as_dict()
            payload["family"] = self.registry.get(feature_id).family.value
            payload["decay_half_life"] = decay_half_life
            governance.append(payload)

        promoted = sum(row["status"] == "PROMOTE_RESEARCH" for row in governance)
        vif_payload = {
            key: (float(value) if np.isfinite(value) else None)
            for key, value in vif_series.items()
        }
        return AlphaFactoryV231Result(
            status="READY" if governance else "EMPTY",
            feature_count=len(governance),
            promoted_count=int(promoted),
            rejected_count=int(len(governance) - promoted),
            governance=tuple(governance),
            clusters=clusters,
            vif=vif_payload,
        )

    def write_report(self, result: AlphaFactoryV231Result, output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        return path


__all__ = ["AlphaFactoryV231", "AlphaFactoryV231Result"]
