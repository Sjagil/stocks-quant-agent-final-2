from __future__ import annotations

import csv
import json
from pathlib import Path

from .health_v2_39_2 import assess_entity_hardened_v2392
from .store_v2_39 import ResearchStoreV239, utc_now


def _write(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = sorted({k for r in rows for k in r if not isinstance(r.get(k), (dict, list, tuple))})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in keys} for r in rows)


def export_snapshot_v2392(runtime_root: Path, store: ResearchStoreV239, *, cfg: dict) -> dict:
    runtime_root.mkdir(parents=True, exist_ok=True)
    assessments: list[dict] = []
    for entity in store.list_entities():
        if not entity.get("is_active"):
            continue
        a = assess_entity_hardened_v2392(
            store,
            entity["entity_id"],
            policy=cfg["health"],
            bayesian=cfg["bayesian"],
            quality_weights=cfg["quality_weights"],
        )
        d = a.as_dict()
        d["role"] = entity["role"]
        d["family"] = entity["family"]
        assessments.append(d)

    flat: list[dict] = []
    for a in assessments:
        flat.append({
            "entity_id": a["entity_id"],
            "role": a["role"],
            "family": a["family"],
            "health": a["health"],
            "recommendation": a["recommendation"],
            "quality_score": a["quality_score"],
            "promotion_readiness_score": a["promotion_readiness_score"],
            "gate_passed": a["gate_passed"],
            "shadow_trades": a["shadow_trades"],
            "independent_classes": a["independent_classes"],
            "independent_sources": a["independent_sources"],
            "promotion_classes": a["promotion_classes"],
            "promotion_sources": a["promotion_sources"],
            "fresh_decision_classes": "|".join(a["fresh_decision_classes"]),
            "posterior_net_edge_bps": a["posterior_net_edge_bps"],
            "oos_observations": a["quality_diagnostics"].get("oos_observations", 0),
            "max_positive_cost_stress_multiplier": a["quality_diagnostics"].get("max_positive_cost_stress_multiplier", 0.0),
            "blockers": "|".join(a["blockers"]),
            "warnings": "|".join(a["warnings"]),
            "missing_requirements": "|".join(a["missing_requirements"]),
            "positive_reasons": "|".join(a["positive_reasons"]),
        })

    _write(runtime_root / "quality_scorecard_v2_39_2.csv", flat)
    _write(runtime_root / "champion_review_queue_v2_39_2.csv", [x for x in flat if x["recommendation"] == "RECOMMEND_CHAMPION_REVIEW"])
    _write(runtime_root / "evidence_gaps_v2_39_2.csv", [x for x in flat if x["missing_requirements"]])
    _write(runtime_root / "retirement_watch_v2_39_2.csv", [x for x in flat if "RETIRE" in x["recommendation"] or "DEACTIVATE" in x["recommendation"]])

    status = {
        "schema": "continuous_quant_research_status_v2_39_2",
        "generated_at": utc_now(),
        "counts": store.counts(),
        "assessments": assessments,
        "recommendations": store.latest_recommendations()[:20],
        "champion_review_count": sum(a["recommendation"] == "RECOMMEND_CHAMPION_REVIEW" for a in assessments),
        "automatic_champion_promotion": False,
        "automatic_live_promotion": False,
        "broker_submission_enabled": False,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (runtime_root / "status_v2_39_2.json").write_text(json.dumps(status, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        "# Continuous Quant Research v2.39.2",
        "",
        f"Generated: {status['generated_at']}",
        "",
        f"Champion reviews eligible: {status['champion_review_count']}",
        "",
        "## Evidence-semantic assessments",
        "",
    ]
    for x in sorted(flat, key=lambda y: (y["gate_passed"], y["promotion_readiness_score"], y["quality_score"]), reverse=True)[:30]:
        lines.append(
            f"- `{x['entity_id']}` — **{x['recommendation']}** — quality {x['quality_score']:.3f} — "
            f"readiness {x['promotion_readiness_score']:.3f} — missing: {x['missing_requirements'] or 'none'}"
        )
    lines += ["", "Execution authority: **NONE**", "Automatic champion promotion: **false**", "Automatic live promotion: **false**"]
    (runtime_root / "status_v2_39_2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return status


__all__ = ["export_snapshot_v2392"]
