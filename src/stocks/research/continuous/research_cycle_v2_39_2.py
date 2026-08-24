from __future__ import annotations

import json
from pathlib import Path

from .artifact_evidence_bridge_v2_39_1 import sync_known_artifact_evidence
from .candidate_sync_v2_39 import sync_candidate_registry
from .export_v2_39_2 import export_snapshot_v2392
from .health_v2_39_2 import assess_entity_hardened_v2392
from .job_runner_v2_39_2 import execute_jobs_v2392
from .scheduler_v2_39 import next_due, schedule_discovery_if_due, schedule_due_entity_reviews
from .shadow_ingest_v2_39 import ingest_shadow_inbox
from .store_v2_39 import ResearchStoreV239


def load_config_v2392(project_root: Path, config_path=None):
    path = Path(config_path) if config_path else project_root / "config/continuous_quant_research_v2_39_2.json"
    if not path.is_absolute():
        path = project_root / path
    cfg = json.loads(path.read_text())
    if (
        cfg.get("execution_authority") != "NONE"
        or cfg.get("automatic_live_promotion")
        or cfg.get("automatic_champion_promotion")
        or cfg.get("broker_submission_enabled")
    ):
        raise ValueError("v2.39.2 config attempted to escalate authority")
    return cfg


def runtime_paths_v2392(project_root: Path, cfg: dict):
    runtime_root = project_root / cfg.get("runtime_root", "artifacts/research_runtime/continuous_quant_research_v2_39")
    return runtime_root, runtime_root / cfg.get("database_name", "research.db")


def recompute_all_v2392(store: ResearchStoreV239, cfg: dict) -> int:
    count = 0
    for entity in store.list_entities(active_only=True):
        assessment = assess_entity_hardened_v2392(
            store,
            entity["entity_id"],
            policy=cfg["health"],
            bayesian=cfg["bayesian"],
            quality_weights=cfg["quality_weights"],
        )
        due = entity.get("next_due_at") or next_due(entity, cfg["scheduler"])
        store.set_entity_health(entity["entity_id"], assessment.health, next_due_at=due)
        store.add_recommendation(entity["entity_id"], assessment.recommendation, assessment.score, assessment.reasons)
        count += 1
    return count


def run_research_cycle_v2392(
    project_root: Path,
    *,
    run_discovery: bool = False,
    execute_ready: bool = True,
    max_jobs: int = 50,
    limit=None,
    as_of=None,
    config_path=None,
):
    cfg = load_config_v2392(project_root, config_path)
    runtime_root, db = runtime_paths_v2392(project_root, cfg)
    store = ResearchStoreV239(db)
    cycle_id = store.begin_cycle()
    summary = {
        "cycle_id": cycle_id,
        "schema": "continuous_quant_research_cycle_v2_39_2",
        "run_discovery": bool(run_discovery),
    }
    try:
        if run_discovery:
            summary["discovery_scheduled"] = schedule_discovery_if_due(
                store,
                cfg["scheduler"],
                force=True,
                limit=int(limit or cfg["discovery"].get("default_limit", 150)),
                as_of=as_of,
            )
            summary["discovery_jobs"] = execute_jobs_v2392(
                project_root,
                store,
                max_jobs=1,
                scheduler_policy=cfg["scheduler"],
                health_policy=cfg["health"],
                bayesian=cfg["bayesian"],
                quality_weights=cfg["quality_weights"],
            )
        summary["candidate_sync"] = sync_candidate_registry(project_root, store, rebuild=True)
        summary["artifact_evidence_sync"] = (
            sync_known_artifact_evidence(project_root, store)
            if cfg.get("artifact_evidence_bridge", {}).get("enabled", True)
            else {"disabled": True}
        )
        summary["shadow_ingest"] = ingest_shadow_inbox(
            project_root,
            store,
            list(cfg.get("inbox", {}).get("shadow_feedback_globs", [])),
        )
        summary["health_recomputed"] = recompute_all_v2392(store, cfg)
        summary["entity_reviews_scheduled"] = schedule_due_entity_reviews(store, cfg["scheduler"])
        if execute_ready:
            summary["jobs"] = execute_jobs_v2392(
                project_root,
                store,
                max_jobs=max_jobs,
                scheduler_policy=cfg["scheduler"],
                health_policy=cfg["health"],
                bayesian=cfg["bayesian"],
                quality_weights=cfg["quality_weights"],
            )
        summary["status"] = export_snapshot_v2392(runtime_root, store, cfg=cfg)
        store.finish_cycle(cycle_id, status="SUCCEEDED", summary=summary)
    except Exception as exc:
        summary["error"] = f"{type(exc).__name__}: {exc}"
        store.finish_cycle(cycle_id, status="FAILED", summary=summary)
        raise
    (runtime_root / "cycle_audit_v2_39_2.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return summary


__all__ = ["load_config_v2392", "runtime_paths_v2392", "recompute_all_v2392", "run_research_cycle_v2392"]
