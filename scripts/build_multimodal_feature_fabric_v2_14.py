#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.agents.candle_fabric import frame_for_timeframe
from stocks.agents.feature_fabric import (
    append_pit_context_snapshot,
    build_current_context_snapshot,
)
from stocks.agents.feature_views import ROLE_COLUMNS, select_role_features
from stocks.rl.features import build_rl_features

ROOT = Path(__file__).resolve().parents[1]


def queue_symbols(limit: int) -> list[str]:
    path = ROOT / "artifacts/research_runtime/agent_training_queue_v2_13/queue.csv"
    if not path.is_file():
        return []
    frame = pd.read_csv(path)
    return [str(value).upper() for value in frame["symbol"].head(limit)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols")
    parser.add_argument("--from-queue", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--append-pit", action="store_true")
    args = parser.parse_args()

    if args.from_queue or not args.symbols:
        symbols = queue_symbols(max(1, int(args.limit)))
    else:
        symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    if not symbols:
        raise SystemExit("no symbols resolved; build the v2.13 queue or pass --symbols")

    rows = []
    snapshots = []
    for symbol in symbols:
        frame = frame_for_timeframe(ROOT, symbol, args.timeframe)
        bank = build_rl_features(frame)
        snapshot = build_current_context_snapshot(ROOT, symbol, args.timeframe)
        snapshots.append(snapshot.to_dict())
        if args.append_pit:
            append_pit_context_snapshot(ROOT, snapshot)

        role_metrics = {}
        for role in ROLE_COLUMNS:
            view = select_role_features(bank, role)
            role_metrics[role] = {
                "features": int(view.shape[1]),
                "usable_rows": int(len(view.dropna())),
            }
        availability = {item.name: item.available for item in snapshot.modalities}

        rows.append(
            {
                "symbol": symbol,
                "timeframe": args.timeframe,
                "raw_candle_rows": int(len(frame)),
                "feature_bank_columns": int(bank.shape[1]),
                "dqn_features": role_metrics["DQN_TIMING"]["features"],
                "dqn_usable_rows": role_metrics["DQN_TIMING"]["usable_rows"],
                "sac_features": role_metrics["SAC_SIZING"]["features"],
                "sac_usable_rows": role_metrics["SAC_SIZING"]["usable_rows"],
                "risk_features": role_metrics["RISK"]["features"],
                "risk_usable_rows": role_metrics["RISK"]["usable_rows"],
                "news_available": availability.get("news", False),
                "gex_available": availability.get("gex", False),
                "orderflow_available": availability.get("orderflow", False),
                "fundamental_available": availability.get("fundamental", False),
                "macro_available": availability.get("macro", False),
                "sec_available": availability.get("sec", False),
                "context_score": snapshot.score,
                "context_confidence": snapshot.confidence,
                "context_modifier": snapshot.modifier,
                "current_external_context_training_safe": False,
                "execution_authority": "NONE",
            }
        )

    output = ROOT / "artifacts/research_runtime/multimodal_feature_fabric_v2_14"
    output.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(output / "feature_coverage.csv", index=False)
    (output / "current_context.json").write_text(
        json.dumps(
            {
                "schema": "multimodal_feature_context_v2_14",
                "snapshots": snapshots,
                "current_external_context_training_safe": False,
                "execution_authority": "NONE",
            },
            indent=2,
            sort_keys=True,
            default=str,
        ) + "\n",
        encoding="utf-8",
    )

    print("MULTIMODAL_FEATURE_FABRIC_V2_14 SYMBOLS", len(result), "TIMEFRAME", args.timeframe)
    print(result.to_string(index=False))
    print("CURRENT_EXTERNAL_CONTEXT_TRAINING_SAFE False")
    print("PIT_APPEND", bool(args.append_pit))
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
