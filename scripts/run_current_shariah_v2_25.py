#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from stocks.research.pit_shariah_eligibility_v2_25 import (
    build_attestation_queue_v225,
    current_verification_to_pit_events_v225,
)
from stocks.research.shariah_financial_verification import run_verification

ROOT = Path(__file__).resolve().parents[1]
SIGNAL_PATH = ROOT / "artifacts/research_runtime/dynamic_validated_forward_signal_state_v2_24/signals.csv"
MATRIX_PATH = ROOT / "artifacts/research_runtime/candidate_strategy_matrix/matrix.csv"
CANDIDATE_PATH = ROOT / "artifacts/research_runtime/contextual_discovery/candidates.csv"
COMPAT_OUTPUT = ROOT / "artifacts/research_runtime/shariah_financial_verification"
PIT_OUTPUT = ROOT / "artifacts/research_runtime/pit_shariah_eligibility_v2_25/current"


def _symbols(limit: int) -> list[str]:
    frames: list[pd.DataFrame] = []
    if SIGNAL_PATH.is_file():
        signals = pd.read_csv(SIGNAL_PATH)
        if not signals.empty and "symbol" in signals:
            frames.append(signals)
    if MATRIX_PATH.is_file():
        matrix = pd.read_csv(MATRIX_PATH)
        if not matrix.empty and "symbol" in matrix:
            if "research_opportunity" in matrix:
                preferred = matrix.loc[matrix["research_opportunity"].fillna(False).astype(bool)]
                frames.append(preferred if not preferred.empty else matrix)
            else:
                frames.append(matrix)
    if CANDIDATE_PATH.is_file():
        candidates = pd.read_csv(CANDIDATE_PATH)
        if not candidates.empty and "symbol" in candidates:
            if "contextual_score" in candidates:
                candidates = candidates.sort_values("contextual_score", ascending=False)
            frames.append(candidates)
    result: list[str] = []
    seen: set[str] = set()
    for frame in frames:
        for raw in frame["symbol"].dropna().astype(str):
            symbol = raw.upper().strip()
            if symbol and symbol not in seen:
                seen.add(symbol)
                result.append(symbol)
                if len(result) >= limit:
                    return result
    return result


def _market_caps() -> dict[str, float]:
    if not CANDIDATE_PATH.is_file():
        return {}
    frame = pd.read_csv(CANDIDATE_PATH)
    if frame.empty or not {"symbol", "market_cap"}.issubset(frame.columns):
        return {}
    result: dict[str, float] = {}
    for row in frame.to_dict(orient="records"):
        try:
            value = float(row.get("market_cap"))
        except (TypeError, ValueError):
            continue
        if pd.notna(value) and value > 0:
            result[str(row["symbol"]).upper().strip()] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=datetime.now(UTC).isoformat())
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be positive")
    symbols = _symbols(args.limit)
    if not symbols:
        print("PIT_SHARIAH_CURRENT_V2_25 BLOCKED NO_CANDIDATE_SYMBOLS")
        return 2

    frame, audit = run_verification(
        ROOT,
        symbols=symbols,
        as_of=args.as_of,
        market_caps=_market_caps(),
    )
    audit = {
        **audit,
        "schema": "pit_shariah_current_verification_v2_25",
        "candidate_scope": "DYNAMIC_FORWARD_SIGNAL_UNIVERSE_FIRST",
        "automatic_attestation": False,
        "automatic_live_promotion": False,
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }
    queue = build_attestation_queue_v225(frame)
    events = current_verification_to_pit_events_v225(
        frame,
        decision_time=args.as_of,
    )

    # Keep the canonical compatibility artifact used by the v2.24 portfolio gateway.
    COMPAT_OUTPUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(COMPAT_OUTPUT / "verification.csv", index=False)
    queue.to_csv(COMPAT_OUTPUT / "attestation_queue.csv", index=False)
    (COMPAT_OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    PIT_OUTPUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(PIT_OUTPUT / "verification.csv", index=False)
    events.to_csv(PIT_OUTPUT / "current_events.csv", index=False)
    queue.to_csv(PIT_OUTPUT / "attestation_queue.csv", index=False)
    (PIT_OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    verified = int(frame["trade_eligible"].fillna(False).astype(bool).sum()) if not frame.empty else 0
    pending = int(frame["status"].astype(str).eq("FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED").sum()) if not frame.empty else 0
    print(
        "PIT_SHARIAH_CURRENT_V2_25",
        "SYMBOLS", len(symbols),
        "VERIFIED", verified,
        "PENDING_ATTESTATION", pending,
        "QUEUE", len(queue),
    )
    print("AUTOMATIC_ATTESTATION", False)
    print("BROKER_CALLS", 0)
    print("ORDER_CALLS", 0)
    print("EXECUTION_AUTHORITY", "NONE")
    print("OUTPUT", PIT_OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
