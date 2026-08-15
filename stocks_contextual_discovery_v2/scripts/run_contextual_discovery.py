#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from stocks.integrations import IntegrationRegistry, IntegrationRunner
from stocks.research.contextual_discovery import ContextualDiscoveryPolicy, canonicalize_contextual_candidates
from stocks.research.validated_strategy_registry import write_validated_strategy_registry
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--as-of", default=None); parser.add_argument("--limit", type=int, default=150); args = parser.parse_args()
    strategy_frame, strategy_audit, strategy_path = write_validated_strategy_registry(ROOT)
    policy = ContextualDiscoveryPolicy.load(ROOT / "config" / "contextual_discovery.json")
    if args.limit > policy.maximum_candidates: raise ValueError("requested limit exceeds contextual policy maximum")
    payload = {"limit": int(args.limit), "minimum_total_score": policy.minimum_research_pool_total_score}
    if args.as_of: payload["as_of"] = args.as_of
    registry = IntegrationRegistry.load(ROOT / "config" / "integrations.yaml")
    response = IntegrationRunner(registry).run("stocks_context_reference", "discovery_context", payload, raise_on_error=True)
    artifact_path = next((Path(a.path) for a in response.artifacts if Path(a.path).name == "stocks_reference_contextual_candidates_v2.json"), None)
    if artifact_path is None or not artifact_path.is_file(): raise FileNotFoundError("contextual reference screener artifact missing")
    raw = json.loads(artifact_path.read_text(encoding="utf-8")); frame, audit = canonicalize_contextual_candidates(raw, policy)
    finalists = strategy_frame["promotion_stage"] == "FINALIST_CANDIDATE"
    audit.update({"validated_strategy_count": int(finalists.sum()), "validated_hypothesis_ids": strategy_frame.loc[finalists, "hypothesis_id"].astype(str).tolist(), "strategy_registry": str(strategy_path), "strategy_registry_live_ready": bool(strategy_audit["live_ready"]), "donor_screened_count": int(raw.get("screened_count", 0)), "donor_research_pool_count": int(raw.get("research_pool_count", 0)), "donor_macro_regime": raw.get("macro_regime", "UNKNOWN"), "donor_macro_data_status": raw.get("macro_data_status", "DATA_INCOMPLETE"), "donor_sec_error": raw.get("sec_error")})
    output_root = ROOT / "artifacts" / "research_runtime" / "contextual_discovery"; output_root.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_root / "candidates.csv", index=False); frame.to_parquet(output_root / "candidates.parquet", index=False)
    (output_root / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print("CONTEXTUAL_DISCOVERY_V2", "CANDIDATES", audit["candidate_count"], "CORE", audit["core_count"], "GEMS", audit["gem_count"], "TACTICAL", audit["tactical_count"], "WATCHLIST", audit["watchlist_count"], "NEUTRAL_SOURCE", audit["neutral_source_count"], "MACRO", audit["donor_macro_regime"], "SEC_COVERED", audit["sec_covered_count"])
    if not frame.empty:
        cols = ["symbol","asset_type","lane","source_classification","contextual_score","total_score","fundamental_score","technical_score","macro_score","macro_regime","sec_overlay_points","sec_event_count","market_cap","daily_return","shariah_status"]
        print(frame[cols].head(50).to_string(index=False))
    print("ARTIFACT_ROOT", output_root); return 0
if __name__ == "__main__": raise SystemExit(main())
