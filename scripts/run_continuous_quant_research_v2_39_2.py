#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.research.continuous.artifact_evidence_bridge_v2_39_1 import sync_known_artifact_evidence
from stocks.research.continuous.candidate_sync_v2_39 import sync_candidate_registry
from stocks.research.continuous.drift_ingest_v2_39 import compute_and_store_drift
from stocks.research.continuous.evidence_v2_39 import ingest_evidence_records, load_records
from stocks.research.continuous.export_v2_39_2 import export_snapshot_v2392
from stocks.research.continuous.health_v2_39_2 import assess_entity_hardened_v2392
from stocks.research.continuous.research_cycle_v2_39_2 import (
    load_config_v2392,
    run_research_cycle_v2392,
    runtime_paths_v2392,
)
from stocks.research.continuous.runtime_lock_v2_39 import exclusive_runtime_lock
from stocks.research.continuous.shadow_ingest_v2_39 import ingest_shadow_file
from stocks.research.continuous.store_v2_39 import ResearchStoreV239


def context(args):
    cfg = load_config_v2392(ROOT, args.config)
    runtime_root, db = runtime_paths_v2392(ROOT, cfg)
    return cfg, runtime_root, ResearchStoreV239(db)


def assessment(cfg, store, entity_id):
    return assess_entity_hardened_v2392(
        store,
        entity_id,
        policy=cfg["health"],
        bayesian=cfg["bayesian"],
        quality_weights=cfg["quality_weights"],
    )


def main():
    parser = argparse.ArgumentParser(description="Continuous Quant Research Engine v2.39.2 evidence-semantic hardened")
    parser.add_argument("--config", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    cycle = sub.add_parser("cycle")
    cycle.add_argument("--run-discovery", action="store_true")
    cycle.add_argument("--max-jobs", type=int, default=50)
    cycle.add_argument("--limit", type=int, default=None)
    cycle.add_argument("--as-of", default=None)
    cycle.add_argument("--no-execute-ready", action="store_true")
    sub.add_parser("status")
    explain = sub.add_parser("explain")
    explain.add_argument("--entity-id", required=True)
    queue = sub.add_parser("review-queue")
    queue.add_argument("--limit", type=int, default=50)
    register = sub.add_parser("register")
    register.add_argument("--entity-id", required=True)
    register.add_argument("--entity-type", required=True)
    register.add_argument("--family", default="UNKNOWN")
    register.add_argument("--source", default="MANUAL")
    ingest = sub.add_parser("ingest-evidence")
    ingest.add_argument("--file", required=True)
    shadow = sub.add_parser("ingest-shadow")
    shadow.add_argument("--file", required=True)
    drift = sub.add_parser("drift")
    drift.add_argument("--entity-id", required=True)
    drift.add_argument("--reference", required=True)
    drift.add_argument("--current", required=True)
    drift.add_argument("--features", nargs="*")
    approve = sub.add_parser("approve-role")
    approve.add_argument("--entity-id", required=True)
    approve.add_argument("--role", choices=["CANDIDATE", "CHALLENGER", "CHAMPION", "RETIRED"], required=True)
    approve.add_argument("--reason", required=True)
    sub.add_parser("sync")
    sub.add_parser("sync-artifacts")
    exp = sub.add_parser("experiment")
    exp.add_argument("--entity-id", default=None)
    exp.add_argument("--type", required=True)
    exp.add_argument("--hypothesis", required=True)
    exp.add_argument("--config-json", default="{}")
    exp_result = sub.add_parser("experiment-result")
    exp_result.add_argument("--experiment-id", required=True)
    exp_result.add_argument("--status", choices=["RUNNING", "SUCCEEDED", "FAILED", "REJECTED"], required=True)
    exp_result.add_argument("--result-ref", default=None)
    sub.add_parser("doctor")
    watch = sub.add_parser("watch")
    watch.add_argument("--interval-seconds", type=int, default=3600)
    watch.add_argument("--discovery-every", type=int, default=24)
    watch.add_argument("--max-jobs", type=int, default=50)

    args = parser.parse_args()
    cfg, runtime_root, store = context(args)

    if args.cmd == "init":
        export_snapshot_v2392(runtime_root, store, cfg=cfg)
        print("V2_39_2_INIT_OK", store.path)
        return 0
    if args.cmd == "cycle":
        print(json.dumps(run_research_cycle_v2392(
            ROOT,
            run_discovery=args.run_discovery,
            execute_ready=not args.no_execute_ready,
            max_jobs=args.max_jobs,
            limit=args.limit,
            as_of=args.as_of,
            config_path=args.config,
        ), indent=2, default=str))
        return 0
    if args.cmd == "status":
        print(json.dumps(export_snapshot_v2392(runtime_root, store, cfg=cfg), indent=2, default=str))
        return 0
    if args.cmd == "explain":
        print(json.dumps(assessment(cfg, store, args.entity_id).as_dict(), indent=2, default=str))
        return 0
    if args.cmd == "review-queue":
        rows = [assessment(cfg, store, e["entity_id"]).as_dict() for e in store.list_entities(active_only=True)]
        rows = sorted(rows, key=lambda x: (x["gate_passed"], x["promotion_readiness_score"], x["score"]), reverse=True)[:args.limit]
        print(json.dumps(rows, indent=2, default=str))
        return 0
    if args.cmd == "register":
        store.register_manual(args.entity_id, args.entity_type, args.family, args.source)
        print("REGISTERED", args.entity_id)
        return 0
    if args.cmd == "ingest-evidence":
        print(json.dumps(ingest_evidence_records(store, load_records(args.file)), indent=2))
        return 0
    if args.cmd == "ingest-shadow":
        print(json.dumps(ingest_shadow_file(store, args.file), indent=2))
        return 0
    if args.cmd == "drift":
        print(json.dumps(compute_and_store_drift(store, args.entity_id, args.reference, args.current, features=args.features or None), indent=2))
        return 0
    if args.cmd == "approve-role":
        if args.role == "CHAMPION":
            a = assessment(cfg, store, args.entity_id)
            if not a.gate_passed:
                print(json.dumps({"error": "CHAMPION_GATE_NOT_PASSED", "assessment": a.as_dict()}, indent=2))
                return 3
        store.set_role_manual(args.entity_id, args.role, args.reason)
        print("ROLE_SET", args.entity_id, args.role)
        return 0
    if args.cmd == "sync":
        print(json.dumps(sync_candidate_registry(ROOT, store, rebuild=True), indent=2, default=str))
        return 0
    if args.cmd == "sync-artifacts":
        print(json.dumps(sync_known_artifact_evidence(ROOT, store), indent=2, default=str))
        return 0
    if args.cmd == "experiment":
        experiment_id = store.register_experiment(
            entity_id=args.entity_id,
            experiment_type=args.type,
            hypothesis=args.hypothesis,
            config=json.loads(args.config_json),
        )
        print("EXPERIMENT_REGISTERED", experiment_id)
        return 0
    if args.cmd == "experiment-result":
        store.update_experiment(args.experiment_id, status=args.status, result_ref=args.result_ref)
        print("EXPERIMENT_UPDATED", args.experiment_id, args.status)
        return 0
    if args.cmd == "doctor":
        checks = {
            "db_exists": store.path.is_file(),
            "config_authority_none": cfg.get("execution_authority") == "NONE",
            "automatic_live_promotion_false": not cfg.get("automatic_live_promotion"),
            "automatic_champion_promotion_false": not cfg.get("automatic_champion_promotion"),
            "broker_submission_false": not cfg.get("broker_submission_enabled"),
            "quality_weights_sum_1": abs(sum(cfg["quality_weights"].values()) - 1.0) < 1e-9,
            "promotion_evidence_classes_ge_2": cfg["health"].get("minimum_independent_evidence_classes", 0) >= 2,
            "promotion_evidence_sources_ge_2": cfg["health"].get("minimum_independent_evidence_sources", 0) >= 2,
            "minimum_oos_observations_ge_60": cfg["health"].get("minimum_oos_observations", 0) >= 60,
            "cost_stress_gate_ge_2x": cfg["health"].get("minimum_cost_stress_multiplier", 0) >= 2.0,
            "parallel_research_script": (ROOT / "scripts/run_parallel_research.py").is_file(),
            "candidate_registry_builder": (ROOT / "scripts/build_research_candidate_registry.py").is_file(),
        }
        checks["ready"] = all(checks.values())
        print(json.dumps(checks, indent=2))
        return 0 if checks["ready"] else 2
    if args.cmd == "watch":
        if args.interval_seconds < 60:
            raise SystemExit("watch interval must be >= 60 seconds")
        with exclusive_runtime_lock(runtime_root / "research_v2_39_2.lock"):
            print("V2_39_2_WATCH_RUNNING", "interval", args.interval_seconds, "seconds")
            iteration = 0
            while True:
                run_discovery = iteration % max(1, int(args.discovery_every * 3600 / args.interval_seconds)) == 0
                try:
                    run_research_cycle_v2392(ROOT, run_discovery=run_discovery, max_jobs=args.max_jobs, config_path=args.config)
                except Exception as exc:
                    print("CYCLE_FAILED", type(exc).__name__, exc, file=sys.stderr)
                iteration += 1
                time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
