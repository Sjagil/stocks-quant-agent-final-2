#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env
from stocks.providers.fabric import SourceFabric
from stocks.providers.federation_v2_27 import (
    SCHEMA,
    extract_news_items,
    integration_summary,
    provider_inventory,
    sanitize_exception_text,
    sanitize_payload,
    summarize_source_fabric,
    symbols_from_csv,
    universe_metadata,
    write_json,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "artifacts/research_runtime/"
    "provider_federation_v2_27"
)


def _safe_integration(
    runner: IntegrationRunner,
    name: str,
    action: str,
    payload: dict | None = None,
    *,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    try:
        response = runner.run(
            name,
            action,
            payload or {},
            timeout_seconds=timeout_seconds,
        )
        return integration_summary(
            response
        )
    except Exception as exc:
        return {
            "state": "ERROR",
            "ok": False,
            "error": sanitize_exception_text(
                exc
            ),
            "warnings": [
                "INTEGRATION_EXCEPTION_ISOLATED"
            ],
            "data": {},
            "artifacts": [],
        }


def _empty_fabric(
    symbols: list[str],
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "schema": (
            "source_fabric_refresh_v3_"
            "degraded"
        ),
        "created_at": (
            datetime.now(UTC).isoformat()
        ),
        "execution_authority": "NONE",
        "broker_order_calls": 0,
        "symbols": {
            symbol: {
                "symbol": symbol,
                "results": [],
            }
            for symbol in symbols
        },
        "global": {"results": []},
        "research_engines": {},
        "fabric_error": (
            sanitize_exception_text(exc)
        ),
        "artifact": None,
    }


def main() -> int:
    load_project_env(ROOT)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols-from",
        default=str(
            ROOT
            / "artifacts/research_runtime/"
            "contextual_1h_hydration/"
            "usable_candidates.csv"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
    )
    parser.add_argument(
        "--as-of",
        default=(
            datetime.now(UTC)
            .date()
            .isoformat()
        ),
    )
    parser.add_argument(
        "--donor-lookback-days",
        type=int,
        default=90,
    )
    parser.add_argument(
        "--macro-lookback-years",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--skip-options-context",
        action="store_true",
    )
    args = parser.parse_args()

    symbols = symbols_from_csv(
        args.symbols_from,
        limit=args.limit,
    )
    if not symbols:
        print(
            "PROVIDER_FEDERATION_V2_27_3 "
            "BLOCKED ZERO_SYMBOLS"
        )
        return 2

    fabric_error = None
    try:
        fabric_payload = (
            SourceFabric(ROOT).run(
                tuple(symbols),
                include_engines=True,
            )
        )
    except Exception as exc:
        fabric_error = (
            sanitize_exception_text(exc)
        )
        fabric_payload = _empty_fabric(
            symbols,
            exc,
        )

    fabric_payload, fabric_security = (
        sanitize_payload(fabric_payload)
    )
    source_summary = (
        summarize_source_fabric(
            fabric_payload
        )
    )
    news_items = extract_news_items(
        fabric_payload
    )
    universe = universe_metadata(
        fabric_payload
    )

    integration_results: dict[
        str, dict[str, Any]
    ] = {}
    registry_error = None

    try:
        registry = IntegrationRegistry.load(
            ROOT / "config/integrations.yaml",
            project_root=ROOT,
        )
        integration_runner = (
            IntegrationRunner(registry)
        )
    except Exception as exc:
        registry_error = (
            sanitize_exception_text(exc)
        )
        integration_runner = None

    macro_start = (
        datetime.fromisoformat(
            args.as_of
        ).date()
        - timedelta(
            days=365
            * max(
                int(
                    args.macro_lookback_years
                ),
                1,
            )
        )
    ).isoformat()

    def run_donor(
        key: str,
        integration: str,
        action: str,
        payload: dict[str, Any],
        timeout: int,
    ) -> None:
        if integration_runner is None:
            integration_results[key] = {
                "state": "UNAVAILABLE",
                "ok": False,
                "error": registry_error,
                "warnings": [
                    "INTEGRATION_REGISTRY_UNAVAILABLE"
                ],
                "data": {},
                "artifacts": [],
            }
            return

        integration_results[key] = (
            _safe_integration(
                integration_runner,
                integration,
                action,
                payload,
                timeout_seconds=timeout,
            )
        )

    run_donor(
        "stocks_macro_refresh",
        "stocks_context_reference",
        "macro_refresh_read_only",
        {
            "start": macro_start,
            "end": args.as_of,
        },
        900,
    )
    run_donor(
        "stocks_screener",
        "stocks_reference",
        "screener_candidates",
        {
            "as_of": args.as_of,
            "limit": 150,
        },
        900,
    )
    run_donor(
        "stocks_contextual_discovery",
        "stocks_context_reference",
        "discovery_context",
        {
            "as_of": args.as_of,
            "limit": 150,
            "minimum_total_score": 45.0,
        },
        900,
    )
    run_donor(
        "stocks_multitimeframe",
        "stocks_reference",
        "multitimeframe_collect",
        {
            "symbols": symbols,
            "intervals": [
                "15m",
                "1h",
                "1d",
            ],
            "providers": [
                "eodhd",
                "yfinance",
            ],
            "lookback_days": int(
                args.donor_lookback_days
            ),
            "end": args.as_of,
        },
        900,
    )
    run_donor(
        "stocks_news_intelligence",
        "stocks_reference",
        "news_link",
        {
            "items": news_items,
            "universe": universe,
        },
        300,
    )

    if not args.skip_options_context:
        run_donor(
            "stocks_market_context",
            "stocks_context_reference",
            "market_context",
            {
                "symbols": symbols,
                "fetch_options": True,
                "max_expirations": 4,
            },
            900,
        )

    integration_results, donor_security = (
        sanitize_payload(
            integration_results
        )
    )

    inventory = provider_inventory()
    configured = [
        row["provider"]
        for row in inventory
        if row["configured"]
    ]

    ok_integrations = sum(
        bool(row.get("ok"))
        for row in (
            integration_results.values()
        )
    )
    failures = [
        name
        for name, row
        in integration_results.items()
        if not row.get("ok")
    ]

    fabric_result_count = sum(
        len(
            symbol_payload.get(
                "results",
                [],
            )
        )
        for symbol_payload
        in (
            fabric_payload.get(
                "symbols",
                {},
            )
            or {}
        ).values()
    )

    context_available = (
        fabric_result_count > 0
        or ok_integrations > 0
    )
    status = (
        "READY"
        if (
            fabric_error is None
            and not failures
            and context_available
        )
        else "DEGRADED"
        if context_available
        else "UNAVAILABLE"
    )

    payload = {
        "schema": SCHEMA,
        "generated_at": (
            datetime.now(UTC).isoformat()
        ),
        "as_of": args.as_of,
        "status": status,
        "symbols": symbols,
        "provider_inventory": inventory,
        "configured_providers": configured,
        "source_fabric_artifact": (
            fabric_payload.get("artifact")
        ),
        "source_fabric_summary": (
            source_summary
        ),
        "source_fabric_news_items": (
            len(news_items)
        ),
        "source_fabric_error": (
            fabric_error
        ),
        "source_fabric_redactions": (
            fabric_security
        ),
        "donor_repo": "references/Stocks",
        "donor_actions": integration_results,
        "donor_action_count": len(
            integration_results
        ),
        "donor_ok_count": ok_integrations,
        "donor_failures": failures,
        "donor_redactions": donor_security,
        "research_context_ready": (
            context_available
        ),
        "research_context_failure_policy": (
            "BEST_EFFORT_FAIL_CLOSED_PER_SOURCE"
        ),
        "market_freshness_authority": (
            "SEPARATE_V2_27_IBKR_BRIDGE"
        ),
        "provider_data_never_substitutes_"
        "market_freshness": True,
        "strategy_authority": "NONE",
        "broker_submission_enabled": False,
        "automatic_live_promotion": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
        "secret_values_logged": False,
    }

    output = write_json(
        OUTPUT / "audit.json",
        payload,
    )

    print(
        "PROVIDER_FEDERATION_V2_27_3",
        "STATUS",
        status,
        "SYMBOLS",
        len(symbols),
        "CONFIGURED_PROVIDERS",
        len(configured),
        "DONOR_ACTIONS",
        len(integration_results),
        "DONOR_OK",
        ok_integrations,
        "DONOR_FAILED",
        len(failures),
    )
    print(
        "SOURCE_FABRIC_NEWS_ITEMS",
        len(news_items),
    )
    print(
        "SOURCE_FABRIC_ERROR",
        fabric_error or "",
    )

    for provider, states in (
        source_summary.get(
            "providers",
            {},
        ).items()
    ):
        formatted = ",".join(
            f"{state}={count}"
            for state, count
            in sorted(states.items())
        )
        print(
            "PROVIDER_STATE",
            provider,
            formatted,
        )

    for name, result in (
        integration_results.items()
    ):
        print(
            "DONOR_ACTION",
            name,
            "STATE",
            result.get("state"),
            "OK",
            bool(result.get("ok")),
            "ERROR",
            result.get("error") or "",
        )

    print(
        "DONOR_FAILURES",
        "|".join(failures),
    )
    print(
        "SECRET_REDACTIONS",
        int(
            fabric_security.get(
                "redaction_count",
                0,
            )
        )
        + int(
            donor_security.get(
                "redaction_count",
                0,
            )
        ),
    )
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", output)

    # Research context is supplementary.  Individual provider failures are
    # recorded and fail closed for that provider, but never invalidate an
    # already-passed market-freshness gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
