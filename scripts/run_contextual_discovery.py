
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.integrations import IntegrationRegistry, IntegrationRunner
from stocks.providers.env import load_project_env, secret
from stocks.research.contextual_discovery import (
    ContextualDiscoveryPolicy,
    canonicalize_contextual_candidates,
)
from stocks.research.eodhd_native_discovery import build_native_contextual_payload
from stocks.research.validated_strategy_registry import write_validated_strategy_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--limit", type=int, default=150)
    args = parser.parse_args()

    strategy_frame, strategy_audit, strategy_path = write_validated_strategy_registry(ROOT)
    policy = ContextualDiscoveryPolicy.load(ROOT / "config/contextual_discovery.json")
    if args.limit > policy.maximum_candidates:
        raise ValueError("requested limit exceeds contextual policy maximum")

    payload = {
        "limit": int(args.limit),
        "minimum_total_score": policy.minimum_research_pool_total_score,
    }
    if args.as_of:
        payload["as_of"] = args.as_of

    registry = IntegrationRegistry.load(ROOT / "config/integrations.yaml")
    response = IntegrationRunner(registry).run(
        "stocks_context_reference",
        "discovery_context",
        payload,
        raise_on_error=True,
    )
    artifact_path = next(
        (
            Path(artifact.path)
            for artifact in response.artifacts
            if Path(artifact.path).name
            == "stocks_reference_contextual_candidates_v2.json"
        ),
        None,
    )
    if artifact_path is None or not artifact_path.is_file():
        raise FileNotFoundError("contextual reference screener artifact missing")

    donor_raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    raw = donor_raw
    context_source = "STOCKS_REFERENCE"
    native_fallback_error = None

    if int(donor_raw.get("screened_count", 0)) == 0:
        try:
            load_project_env(ROOT)
            api_key = secret(
                "EODHD_API_KEY",
                "EOD_API_KEY",
                "EODHISTORICALDATA_API_KEY",
            )
            if not api_key:
                raise ValueError("EODHD API key missing")
            raw = build_native_contextual_payload(
                ROOT,
                api_key=api_key,
                as_of=args.as_of,
                limit=int(args.limit),
            )
            context_source = "EODHD_NATIVE_FALLBACK"
        except Exception as exc:
            native_fallback_error = f"{type(exc).__name__}: {exc}"
            raw = donor_raw

    frame, audit = canonicalize_contextual_candidates(raw, policy)
    finalists = strategy_frame["promotion_stage"] == "FINALIST_CANDIDATE"
    audit.update(
        {
            "context_source": context_source,
            "native_fallback_error": native_fallback_error,
            "validated_strategy_count": int(finalists.sum()),
            "validated_hypothesis_ids": strategy_frame.loc[
                finalists, "hypothesis_id"
            ].astype(str).tolist(),
            "strategy_registry": str(strategy_path),
            "strategy_registry_live_ready": bool(strategy_audit["live_ready"]),
            "donor_screened_count": int(donor_raw.get("screened_count", 0)),
            "donor_research_pool_count": int(
                donor_raw.get("research_pool_count", 0)
            ),
            "source_screened_count": int(raw.get("screened_count", 0)),
            "source_research_pool_count": int(raw.get("research_pool_count", 0)),
            "source_trade_eligible_count": int(raw.get("trade_eligible_count", 0)),
            "source_macro_regime": raw.get("macro_regime", "UNKNOWN"),
            "source_macro_data_status": raw.get(
                "macro_data_status", "DATA_INCOMPLETE"
            ),
            "source_sec_error": raw.get("sec_error"),
            "source_classification_counts": raw.get("classification_counts", {}),
            "source_rejection_reason_counts": raw.get(
                "rejection_reason_counts", {}
            ),
            "source_research_blocker_counts": raw.get(
                "research_blocker_counts", {}
            ),
            "source_shariah_gate_counts": raw.get("shariah_gate_counts", {}),
            "source_inventory": raw.get("source_inventory", {}),
        }
    )

    output_root = ROOT / "artifacts/research_runtime/contextual_discovery"
    output_root.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_root / "candidates.csv", index=False)
    frame.to_parquet(output_root / "candidates.parquet", index=False)
    (output_root / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    if context_source == "EODHD_NATIVE_FALLBACK":
        (output_root / "native_source_payload.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

    print(
        "CONTEXTUAL_DISCOVERY_V2_5",
        "SOURCE", audit["context_source"],
        "DONOR_SCREENED", audit["donor_screened_count"],
        "SOURCE_SCREENED", audit["source_screened_count"],
        "RESEARCH_POOL", audit["source_research_pool_count"],
        "TRADE_ELIGIBLE", audit["trade_eligible_count"],
        "CANDIDATES", audit["candidate_count"],
        "CORE", audit["core_count"],
        "GEMS", audit["gem_count"],
        "TACTICAL", audit["tactical_count"],
        "WATCHLIST", audit["watchlist_count"],
        "PENDING_SHARIAH", audit["pending_shariah_count"],
        "RESEARCH_ONLY", audit["pure_research_count"],
        "SEC_COVERED", audit["sec_covered_count"],
    )
    print("CLASSIFICATIONS", json.dumps(audit["source_classification_counts"], sort_keys=True))
    print("SHARIAH_GATES", json.dumps(audit["source_shariah_gate_counts"], sort_keys=True))
    if native_fallback_error:
        print("NATIVE_FALLBACK_ERROR", native_fallback_error)

    if not frame.empty:
        columns = [
            column
            for column in (
                "symbol",
                "asset_type",
                "lane",
                "research_lane",
                "source_classification",
                "trade_eligible",
                "shariah_gate",
                "contextual_score",
                "research_score",
                "technical_score",
                "liquidity_score",
                "market_cap",
                "daily_return",
                "mover_type",
                "shariah_status",
            )
            if column in frame.columns
        ]
        print(frame[columns].head(50).to_string(index=False))

    print("ARTIFACT_ROOT", output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
