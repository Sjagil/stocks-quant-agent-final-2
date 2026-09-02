from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .contracts_v2_39 import EvidenceRecordV239
from .store_v2_39 import ResearchStoreV239


def ingest_produced_evidence(
    store: ResearchStoreV239,
    *,
    entity_id: str,
    oos_metrics: dict,
    cost_rows: list[dict],
    oos_source_ref: str,
    cost_source_prefix: str,
    as_of: str | None = None,
) -> dict:
    stamp = as_of or datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0
    oos = EvidenceRecordV239(
        entity_id=entity_id,
        evidence_type="PURGED_WALK_FORWARD",
        as_of=stamp,
        metrics=oos_metrics,
        source="purged_walk_forward_v2.39.3",
        source_ref=oos_source_ref,
        sample_count=int(oos_metrics.get("observations", 0)),
    )
    added += int(store.add_evidence(oos))
    cost_added = 0
    for row in cost_rows:
        multiplier = float(row["stress_multiplier"])
        metrics = dict(row)
        metrics["net_edge_bps"] = metrics.get("expectancy_bps")
        record = EvidenceRecordV239(
            entity_id=entity_id,
            evidence_type="EXECUTION_COST_STRESS",
            as_of=stamp,
            metrics=metrics,
            source="v2.36_practical_cost_stress_v2.39.3",
            source_ref=f"{cost_source_prefix}:stress={multiplier:g}x",
            sample_count=int(metrics.get("effective_observations", 0)),
        )
        is_added = int(store.add_evidence(record))
        added += is_added
        cost_added += is_added
    return {"added": int(added), "oos_added": int(added - cost_added), "cost_added": int(cost_added)}


__all__ = ["ingest_produced_evidence"]
