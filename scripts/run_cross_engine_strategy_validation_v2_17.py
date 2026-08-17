#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.research.cross_engine_validation_v2_17 import (
    aggregate_engine_status,
    build_canonical_replay_packet,
    compare_ledgers,
    normalize_external_ledger,
)
from stocks.research.pybroker_crosscheck import replay_contract_audit
from stocks.research.strategy_factory_1h import prepare_one_hour_frame

ROOT = Path(__file__).resolve().parents[1]


def _source_1h(symbol: str) -> Path:
    candidates = (
        ROOT / "data/canonical/provider_fabric" / f"{symbol}_1h.parquet",
        ROOT / "data/adjusted" / f"{symbol}_1h.parquet",
        ROOT / "data/derived" / f"{symbol}_1h.parquet",
        ROOT / "data/processed" / f"{symbol}_1h.parquet",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"{symbol}: missing 1h data")


def _load_frames(symbols: list[str]) -> dict[str, pd.DataFrame]:
    output = {}
    for symbol in symbols:
        raw = pd.read_parquet(_source_1h(symbol))
        output[symbol] = prepare_one_hour_frame(raw, symbol)
    return output


def _finalist_ids(config: dict) -> list[tuple[str, str]]:
    return [
        (
            str(item["hypothesis_id"]),
            str(item["strategy"]),
        )
        for item in config["scope"]["strategies"]
    ]


def _survivor_trades() -> pd.DataFrame:
    candidates = (
        ROOT
        / "artifacts/research_runtime/strategy_factory_1h/"
        "survivor_trades.parquet",
        ROOT
        / "artifacts/research_runtime/candidate_strategy_matrix/"
        "trades.parquet",
    )
    for path in candidates:
        if path.is_file():
            return pd.read_parquet(path)
    raise FileNotFoundError(
        "No canonical survivor trade artifact found. "
        "Run the 1h strategy factory/candidate matrix first."
    )


def _artifact_path(response, suffix: str) -> Path | None:
    for artifact in response.artifacts:
        if artifact.path.endswith(suffix):
            return Path(artifact.path)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--limit-symbols", type=int, default=0)
    parser.add_argument(
        "--engines",
        default="native,pybroker,nautilus,lean",
    )
    args = parser.parse_args()

    config = yaml.safe_load(
        (
            ROOT / "config/cross_engine_strategy_validation_v2_17.yaml"
        ).read_text(encoding="utf-8")
    )
    parity_cfg = config["parity"]
    canonical_cfg = config["canonical_contract"]
    promotion_cfg = config["promotion"]

    requested_engines = tuple(
        value.strip().lower()
        for value in args.engines.split(",")
        if value.strip()
    )
    required = tuple(
        str(value).lower()
        for value in config["engines"]["required"]
    )
    if set(requested_engines) != set(required):
        raise SystemExit(
            "v2.17 strict run requires native,pybroker,nautilus,lean; "
            "use the full engine set for a promotion-capable audit"
        )

    try:
        all_trades = _survivor_trades()
    except FileNotFoundError as exc:
        print(
            "CROSS_ENGINE_PREFLIGHT",
            "READY",
            False,
            "REASON",
            str(exc),
        )
        print("BROKER_CALLS", 0)
        print("ORDER_CALLS", 0)
        print("EXECUTION_AUTHORITY", "NONE")
        return 2
    if "hypothesis_id" not in all_trades:
        raise SystemExit("canonical trade artifact missing hypothesis_id")

    integration_registry = IntegrationRegistry.load(
        ROOT / "config/integrations.yaml",
        project_root=ROOT,
    )
    runner = IntegrationRunner(integration_registry)

    engine_name = {
        "pybroker": "pybroker_reference",
        "nautilus": "nautilus",
        "lean": "lean_reference",
    }

    output_root = (
        ROOT
        / "artifacts/research_runtime/"
        "cross_engine_strategy_validation_v2_17"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    strategy_rows = []
    engine_rows_all = []

    for hypothesis_id, strategy in _finalist_ids(config):
        hypothesis_trades = all_trades.loc[
            all_trades["hypothesis_id"].astype(str) == hypothesis_id
        ].copy()

        if hypothesis_trades.empty:
            print(
                "CROSS_ENGINE_SKIP",
                hypothesis_id,
                strategy,
                "NO_CANONICAL_TRADES",
            )
            continue

        contract = replay_contract_audit(
            hypothesis_trades,
            strategy=strategy,
        )
        if not contract["compatible"]:
            print(
                "CROSS_ENGINE_SKIP",
                hypothesis_id,
                strategy,
                contract["execution_contract"],
                contract["route"],
            )
            continue

        symbols = sorted(
            hypothesis_trades["symbol"]
            .astype(str)
            .str.upper()
            .unique()
            .tolist()
        )
        if args.symbols:
            allowed = {
                value.strip().upper()
                for value in args.symbols.split(",")
                if value.strip()
            }
            symbols = [symbol for symbol in symbols if symbol in allowed]
        if args.limit_symbols > 0:
            symbols = symbols[: args.limit_symbols]

        hypothesis_trades = hypothesis_trades.loc[
            hypothesis_trades["symbol"]
            .astype(str)
            .str.upper()
            .isin(symbols)
        ].copy()

        if hypothesis_trades.empty:
            print(
                "CROSS_ENGINE_SKIP",
                hypothesis_id,
                "ZERO_TRADES_AFTER_SYMBOL_FILTER",
            )
            continue

        frames = _load_frames(symbols)
        schedule, native_ledger, packet_audit = (
            build_canonical_replay_packet(
                frames,
                hypothesis_trades,
                hypothesis_id=hypothesis_id,
                strategy=strategy,
                base_cost_bps_per_side=float(
                    canonical_cfg["common_base_cost_bps_per_side"]
                ),
                stress_cost_bps_per_side=float(
                    canonical_cfg["common_stress_cost_bps_per_side"]
                ),
            )
        )

        strategy_root = output_root / hypothesis_id
        strategy_root.mkdir(parents=True, exist_ok=True)
        schedule_path = strategy_root / "canonical_schedule.parquet"
        native_path = strategy_root / "native_ledger.parquet"
        schedule.to_parquet(schedule_path, index=False)
        native_ledger.to_parquet(native_path, index=False)
        (strategy_root / "packet_audit.json").write_text(
            json.dumps(
                packet_audit,
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        engine_rows = [
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "engine": "native",
                "mode": "FULL_ENGINE_REPLAY",
                "parity": True,
                "symbols": int(native_ledger["base_symbol"].nunique()),
                "trades": int(len(native_ledger)),
                "packet_hash": packet_audit["packet_hash"],
                "bar_hash": packet_audit["bar_hash"],
                "broker_calls": 0,
                "order_calls": 0,
                "execution_authority": "NONE",
            }
        ]

        for engine in ("pybroker", "nautilus", "lean"):
            integration = engine_name[engine]
            print(
                "=" * 78,
                "\nRUN_ENGINE",
                engine,
                hypothesis_id,
                strategy,
            )
            try:
                response = runner.run(
                    integration,
                    "replay_intents",
                    {
                        "schedule_parquet": str(schedule_path),
                        "hypothesis_id": hypothesis_id,
                        "strategy": strategy,
                        "packet_hash": packet_audit["packet_hash"],
                        "bar_hash": packet_audit["bar_hash"],
                    },
                    timeout_seconds=3600,
                    raise_on_error=False,
                )
            except Exception as exc:
                response = None
                engine_rows.append(
                    {
                        "hypothesis_id": hypothesis_id,
                        "strategy": strategy,
                        "engine": engine,
                        "mode": "ENGINE_ERROR",
                        "parity": False,
                        "error": f"{type(exc).__name__}:{exc}",
                        "broker_calls": 0,
                        "order_calls": 0,
                        "execution_authority": "NONE",
                    }
                )
                continue

            if response is None:
                continue

            mode = str(response.data.get("mode") or response.state.value)
            normalized_path = _artifact_path(
                response,
                "normalized_ledger.parquet",
            )

            if (
                normalized_path is None
                or not normalized_path.is_file()
                or mode != "FULL_ENGINE_REPLAY"
            ):
                engine_rows.append(
                    {
                        "hypothesis_id": hypothesis_id,
                        "strategy": strategy,
                        "engine": engine,
                        "mode": mode,
                        "parity": False,
                        "error": response.error,
                        "warnings": "|".join(response.warnings),
                        "broker_calls": 0,
                        "order_calls": 0,
                        "execution_authority": "NONE",
                    }
                )
                continue

            raw_observed = pd.read_parquet(normalized_path)
            observed = normalize_external_ledger(
                raw_observed,
                hypothesis_id=hypothesis_id,
                strategy=strategy,
                base_cost_bps_per_side=float(
                    canonical_cfg["common_base_cost_bps_per_side"]
                ),
                stress_cost_bps_per_side=float(
                    canonical_cfg["common_stress_cost_bps_per_side"]
                ),
            )
            detail, parity = compare_ledgers(
                native_ledger,
                observed,
                max_fill_price_relative_error=float(
                    parity_cfg["max_fill_price_relative_error"]
                ),
                max_trade_return_difference_bps=float(
                    parity_cfg[
                        "max_trade_return_difference_bps"
                    ]
                ),
            )
            detail.to_csv(
                strategy_root / f"{engine}_parity_rows.csv",
                index=False,
            )
            observed.to_parquet(
                strategy_root / f"{engine}_ledger.parquet",
                index=False,
            )
            engine_rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "strategy": strategy,
                    "engine": engine,
                    "mode": mode,
                    **parity,
                    "symbols": int(native_ledger["base_symbol"].nunique()),
                    "trades": int(len(observed)),
                    "packet_hash": packet_audit["packet_hash"],
                    "bar_hash": packet_audit["bar_hash"],
                    "broker_calls": 0,
                    "order_calls": 0,
                    "execution_authority": "NONE",
                }
            )

        aggregate = aggregate_engine_status(
            engine_rows,
            required_engines=required,
            minimum_symbols=int(promotion_cfg["minimum_symbols"]),
            minimum_total_trades=int(
                promotion_cfg["minimum_total_trades"]
            ),
        )
        strategy_rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "strategy": strategy,
                "symbols": int(native_ledger["base_symbol"].nunique()),
                "trades": int(len(native_ledger)),
                "packet_hash": packet_audit["packet_hash"],
                "bar_hash": packet_audit["bar_hash"],
                **aggregate,
            }
        )
        engine_rows_all.extend(engine_rows)

        print(
            "CROSS_ENGINE_RESULT",
            hypothesis_id,
            strategy,
            aggregate["status"],
            "BLOCKERS",
            "|".join(aggregate["blockers"]),
        )

    engine_frame = pd.DataFrame(engine_rows_all)
    summary = pd.DataFrame(strategy_rows)
    engine_frame.to_csv(output_root / "engine_results.csv", index=False)
    summary.to_csv(output_root / "strategy_summary.csv", index=False)

    validated = (
        int(
            (
                summary["status"] == "CROSS_ENGINE_VALIDATED"
            ).sum()
        )
        if not summary.empty
        else 0
    )
    audit = {
        "schema": "cross_engine_strategy_validation_audit_v2_17",
        "strategies": int(len(summary)),
        "validated": validated,
        "required_engines": list(required),
        "cross_engine_reselection": False,
        "parameters_frozen": True,
        "whole_shares_only": True,
        "fractional_shares_allowed": False,
        "fixed_euro_order_cap": False,
        "automatic_live_promotion": False,
        "canonical_broker_writer": config["authority"][
            "canonical_broker_writer"
        ],
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    (output_root / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 78)
    print(
        "CROSS_ENGINE_STRATEGY_VALIDATION_V2_17",
        "STRATEGIES",
        len(summary),
        "VALIDATED",
        validated,
    )
    if not summary.empty:
        print(
            summary[
                [
                    "hypothesis_id",
                    "strategy",
                    "symbols",
                    "trades",
                    "status",
                    "blockers",
                ]
            ].to_string(index=False)
        )
    print("CROSS_ENGINE_RESELECTION False")
    print("WHOLE_SHARES_ONLY True")
    print("FIXED_EURO_ORDER_CAP False")
    print("AUTOMATIC_LIVE_PROMOTION False")
    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
