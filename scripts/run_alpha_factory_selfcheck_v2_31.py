from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stocks.research.alpha_factory_v2_31 import AlphaFactoryV231
from stocks.research.feature_registry_v2_31 import FeatureFamily, FeatureRegistry, FeatureSpec, default_feature_registry
from stocks.research.feature_governance_v2_31 import correlation_clusters
from stocks.research.news_features_v2_31 import NewsEvent, aggregate_news_features


def synthetic_panel() -> pd.DataFrame:
    rng = np.random.default_rng(23131)
    rows: list[dict[str, object]] = []
    for date in range(24):
        regime = "TREND" if date < 12 else "CHOP"
        for asset in range(30):
            feature = rng.normal()
            redundant = feature * 0.99 + rng.normal(scale=0.01)
            noise = rng.normal()
            target = 0.06 * feature + rng.normal(scale=0.035)
            target2 = 0.035 * feature + rng.normal(scale=0.045)
            rows.append(
                {
                    "date": date,
                    "symbol": f"S{asset:02d}",
                    "regime": regime,
                    "signal": feature,
                    "redundant": redundant,
                    "noise": noise,
                    "fwd_1": target,
                    "fwd_2": target2,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    panel = synthetic_panel()
    registry = FeatureRegistry(
        (
            FeatureSpec("signal", FeatureFamily.CROSS_SECTIONAL, "synthetic signal", cross_sectional=True),
            FeatureSpec("redundant", FeatureFamily.CROSS_SECTIONAL, "synthetic redundant", cross_sectional=True),
            FeatureSpec("noise", FeatureFamily.CROSS_SECTIONAL, "synthetic noise", cross_sectional=True),
        )
    )
    result = AlphaFactoryV231(registry=registry).evaluate(
        panel,
        feature_ids=["signal", "noise"],
        date_column="date",
        primary_target="fwd_1",
        forward_targets={1: "fwd_1", 2: "fwd_2"},
    )
    clusters = correlation_clusters(panel[["signal", "redundant", "noise"]], threshold=0.95)
    assert any(set(cluster) == {"signal", "redundant"} for cluster in clusters)
    assert result.promoted_count >= 1
    assert result.execution_authority == "NONE"
    assert len(default_feature_registry().ids()) >= 15

    output = Path("artifacts/research_runtime/alpha_factory_v2_31/selfcheck.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = result.as_dict() | {
        "canonical_registry_feature_count": len(default_feature_registry().ids()),
        "correlation_clusters": [list(cluster) for cluster in clusters],
        "research_compliance_gate_applied": False,
        "broker_submission_enabled": False,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print("ALPHA_FACTORY_V2_31_SELFCHECK OK")
    print("FEATURES", result.feature_count)
    print("PROMOTED", result.promoted_count)
    print("CLUSTERS", len(clusters))
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")


if __name__ == "__main__":
    main()
