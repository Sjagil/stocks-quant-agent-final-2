#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env
from stocks.providers.fabric import SourceFabric
from stocks.providers.federation_v2_27 import (
    SCHEMA,
    assert_payload_contains_no_secrets,
    extract_news_items,
    integration_summary,
    provider_inventory,
    summarize_source_fabric,
    symbols_from_csv,
    universe_metadata,
    write_json,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/research_runtime/provider_federation_v2_27"


def _run_integration(
    runner: IntegrationRunner,
    name: str,
    action: str,
    payload: dict | None = None,
    *,
    timeout_seconds: int | None = None,
):
    return runner.run(
        name,
        action,
        payload or {},
        timeout_seconds=timeout_seconds,
    )


def main() -> int:
    load_project_env(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols-from",
        default=str(ROOT / "artifacts/research_runtime/contextual_1h_hydration/usable_candidates.csv"),
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--as-of", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--donor-lookback-days", type=int, default=90)
    parser.add_argument("--macro-lookback-years", type=int, default=10)
    parser.add_argument("--skip-options-context", action="store_true")
    args = parser.parse_args()

    symbols = symbols_from_csv(args.symbols_from, limit=args.limit)
    if not symbols:
        print("PROVIDER_FEDERATION_V2_27 BLOCKED ZERO_SYMBOLS")
        return 2

    fabric = SourceFabric(ROOT)
    fabric_payload = fabric.run(tuple(symbols), include_engines=True)
    try:
        assert_payload_contains_no_secrets(fabric_payload)
    except Exception:
        artifact = fabric_payload.get("artifact")
        if artifact:
            Path(str(artifact)).unlink(missing_ok=True)
        raise
    source_summary = summarize_source_fabric(fabric_payload)
    news_items = extract_news_items(fabric_payload)
    universe = universe_metadata(fabric_payload)

    registry = IntegrationRegistry.load(ROOT / "config/integrations.yaml", project_root=ROOT)
    runner = IntegrationRunner(registry)
    integration_results: dict[str, dict] = {}

    macro_start = (
        datetime.fromisoformat(args.as_of).date()
        - timedelta(days=365 * max(int(args.macro_lookback_years), 1))
    ).isoformat()
    macro_response = _run_integration(
        runner,
        "stocks_context_reference",
        "macro_refresh_read_only",
        {"start": macro_start, "end": args.as_of},
        timeout_seconds=900,
    )
    integration_results["stocks_macro_refresh"] = integration_summary(macro_response)

    screener_response = _run_integration(
        runner,
        "stocks_reference",
        "screener_candidates",
        {"as_of": args.as_of, "limit": 150},
        timeout_seconds=900,
    )
    integration_results["stocks_screener"] = integration_summary(screener_response)

    discovery_response = _run_integration(
        runner,
        "stocks_context_reference",
        "discovery_context",
        {"as_of": args.as_of, "limit": 150, "minimum_total_score": 45.0},
        timeout_seconds=900,
    )
    integration_results["stocks_contextual_discovery"] = integration_summary(discovery_response)

    mtf_response = _run_integration(
        runner,
        "stocks_reference",
        "multitimeframe_collect",
        {
            "symbols": symbols,
            "intervals": ["15m", "1h", "1d"],
            "providers": ["eodhd", "yfinance"],
            "lookback_days": int(args.donor_lookback_days),
            "end": args.as_of,
        },
        timeout_seconds=900,
    )
    integration_results["stocks_multitimeframe"] = integration_summary(mtf_response)

    news_response = _run_integration(
        runner,
        "stocks_reference",
        "news_link",
        {"items": news_items, "universe": universe},
        timeout_seconds=300,
    )
    integration_results["stocks_news_intelligence"] = integration_summary(news_response)

    if not args.skip_options_context:
        market_response = _run_integration(
            runner,
            "stocks_context_reference",
            "market_context",
            {"symbols": symbols, "fetch_options": True, "max_expirations": 4},
            timeout_seconds=900,
        )
        integration_results["stocks_market_context"] = integration_summary(market_response)

    configured = [row["provider"] for row in provider_inventory() if row["configured"]]
    ok_integrations = sum(bool(row.get("ok")) for row in integration_results.values())
    failures = [name for name, row in integration_results.items() if not row.get("ok")]

    payload = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "as_of": args.as_of,
        "symbols": symbols,
        "provider_inventory": provider_inventory(),
        "configured_providers": configured,
        "source_fabric_artifact": fabric_payload.get("artifact"),
        "source_fabric_summary": source_summary,
        "source_fabric_news_items": len(news_items),
        "donor_repo": "references/Stocks",
        "donor_actions": integration_results,
        "donor_action_count": len(integration_results),
        "donor_ok_count": ok_integrations,
        "donor_failures": failures,
        "research_context_ready": ok_integrations > 0,
        "market_freshness_authority": "SEPARATE_V2_27_IBKR_BRIDGE",
        "strategy_authority": "NONE",
        "broker_submission_enabled": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
        "secret_values_logged": False,
    }
    output = write_json(OUTPUT / "audit.json", payload)

    print(
        "PROVIDER_FEDERATION_V2_27",
        "SYMBOLS", len(symbols),
        "CONFIGURED_PROVIDERS", len(configured),
        "DONOR_ACTIONS", len(integration_results),
        "DONOR_OK", ok_integrations,
        "DONOR_FAILED", len(failures),
    )
    print("SOURCE_FABRIC_NEWS_ITEMS", len(news_items))
    print("DONOR_FAILURES", "|".join(failures))
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", output)
    # Context is best-effort; individual research sources fail closed but do not fake market freshness.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
