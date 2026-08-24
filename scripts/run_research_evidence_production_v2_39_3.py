#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from stocks.research.continuous.evidence_production_export_v2_39_3 import production_status
from stocks.research.continuous.practical_evidence_producer_v2_39_3 import (
    audit_entity_inputs,
    evidence_production_plan,
    load_continuous_config,
    load_production_config,
    produce_due_evidence,
    produce_entity_evidence,
    produce_external_observation_evidence,
    runtime_paths,
)
from stocks.research.continuous.store_v2_39 import ResearchStoreV239


def context(args):
    production = load_production_config(ROOT, args.config)
    continuous = load_continuous_config(ROOT, production)
    _, db, output = runtime_paths(ROOT, production, continuous)
    return production, continuous, output, ResearchStoreV239(db)


def main() -> int:
    parser = argparse.ArgumentParser(description="Practical OOS + execution-cost evidence production v2.39.3")
    parser.add_argument("--config", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    audit = sub.add_parser("audit-inputs")
    audit.add_argument("--entity-id", required=True)
    produce = sub.add_parser("produce")
    produce.add_argument("--entity-id", required=True)
    due = sub.add_parser("produce-due")
    due.add_argument("--max-entities", type=int, default=None)
    plan = sub.add_parser("plan")
    plan.add_argument("--max-entities", type=int, default=20)
    ext = sub.add_parser("produce-from-observations")
    ext.add_argument("--entity-id", required=True)
    ext.add_argument("--file", required=True)
    ext.add_argument("--provenance", required=True)
    ext.add_argument("--base-cost-bps-per-side", type=float, required=True)
    sub.add_parser("status")
    sub.add_parser("doctor")
    args = parser.parse_args()
    production, continuous, output, store = context(args)

    if args.cmd == "audit-inputs":
        print(json.dumps(audit_entity_inputs(ROOT, store, args.entity_id, production_cfg=production).as_dict(), indent=2, default=str))
        return 0
    if args.cmd == "produce":
        result = produce_entity_evidence(ROOT, store, args.entity_id, production_cfg=production, continuous_cfg=continuous)
        print(json.dumps(result.as_dict(), indent=2, default=str))
        return 0 if result.status != "BLOCKED_INPUTS" else 4
    if args.cmd == "produce-due":
        print(json.dumps(produce_due_evidence(ROOT, store, production_cfg=production, continuous_cfg=continuous, max_entities=args.max_entities), indent=2, default=str))
        return 0
    if args.cmd == "plan":
        print(json.dumps(evidence_production_plan(ROOT, store, production_cfg=production, continuous_cfg=continuous, max_entities=args.max_entities), indent=2, default=str))
        return 0
    if args.cmd == "produce-from-observations":
        result = produce_external_observation_evidence(ROOT, store, args.entity_id, observations_file=args.file, provenance_file=args.provenance, base_cost_bps_per_side=args.base_cost_bps_per_side, production_cfg=production, continuous_cfg=continuous)
        print(json.dumps(result.as_dict(), indent=2, default=str))
        return 0
    if args.cmd == "status":
        print(json.dumps(production_status(output), indent=2, default=str))
        return 0
    if args.cmd == "doctor":
        factory_artifacts = (ROOT / production["factory_1h"]["artifact_root"]).is_dir()
        factory_code = (ROOT / "scripts/run_1h_strategy_factory.py").is_file() and (ROOT / "src/stocks/research/strategy_factory_1h.py").is_file() and (ROOT / "src/stocks/research/walkforward_splits.py").is_file()
        external_adapter = (ROOT / "src/stocks/research/continuous/external_oos_evidence_v2_39_3.py").is_file()
        checks = {
            "continuous_db_exists": store.path.is_file(),
            "factory_artifacts_present": factory_artifacts,
            "factory_code_present": factory_code,
            "factory_replay_available": bool(factory_artifacts and factory_code),
            "external_observation_adapter_available": external_adapter,
            "v233_cost_stress_exists": (ROOT / "src/stocks/research/cost_stress_v2_33.py").is_file(),
            "v236_cost_stress_exists": (ROOT / "src/stocks/execution/cost_stress_v2_36.py").is_file(),
            "minimum_effective_oos_ge_60": production.get("minimum_effective_oos_observations", 0) >= 60,
            "required_cost_stress_ge_2x": production["cost_stress"].get("required_multiplier", 0) >= 2.0,
            "authority_none": production.get("execution_authority") == "NONE",
            "broker_submission_false": not production.get("broker_submission_enabled"),
            "automatic_live_promotion_false": not production.get("automatic_live_promotion"),
            "automatic_champion_promotion_false": not production.get("automatic_champion_promotion"),
        }
        core = [
            checks["continuous_db_exists"], checks["v233_cost_stress_exists"], checks["v236_cost_stress_exists"],
            checks["minimum_effective_oos_ge_60"], checks["required_cost_stress_ge_2x"], checks["authority_none"],
            checks["broker_submission_false"], checks["automatic_live_promotion_false"], checks["automatic_champion_promotion_false"],
        ]
        checks["ready"] = all(core) and (checks["factory_replay_available"] or checks["external_observation_adapter_available"])
        print(json.dumps(checks, indent=2))
        return 0 if checks["ready"] else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
