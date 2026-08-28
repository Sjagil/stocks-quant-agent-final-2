#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/research_runtime/cross_engine_strategy_validation_v2_17"


def _parse(value):
    if isinstance(value, (list, dict, tuple)):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    text = str(value).strip()
    if not text:
        return value
    try:
        return ast.literal_eval(text)
    except Exception:
        return value


def main() -> int:
    engine_path = ART / "engine_results.csv"
    summary_path = ART / "strategy_summary.csv"

    if not engine_path.is_file():
        raise SystemExit(f"missing {engine_path}")

    engines = pd.read_csv(engine_path)
    summary = (
        pd.read_csv(summary_path)
        if summary_path.is_file()
        else pd.DataFrame()
    )

    print("=" * 90)
    print("CROSS_ENGINE_FILL_PARITY_DIAGNOSTIC_V2_17_3")

    for row in engines.to_dict(orient="records"):
        engine = str(row.get("engine") or "")
        mode = str(row.get("mode") or "")
        parity = (
            bool(row.get("parity"))
            if pd.notna(row.get("parity"))
            else False
        )
        error = row.get("error")
        warnings = _parse(row.get("warnings"))

        print(
            "ENGINE", engine,
            "MODE", mode,
            "PARITY", parity,
            "TRADES", row.get("trades"),
        )
        if pd.notna(error) and str(error).strip():
            print("  ERROR", str(error))
        if warnings not in (None, "", [], (), {}):
            print("  WARNINGS", warnings)

        for parity_path in sorted(ART.glob(f"*{engine}*parity*.csv")):
            try:
                frame = pd.read_csv(parity_path)
            except Exception as exc:
                print(
                    "  PARITY_READ_ERROR",
                    parity_path.name,
                    repr(exc),
                )
                continue

            print(
                "  PARITY_FILE",
                parity_path.name,
                "ROWS",
                len(frame),
            )
            if frame.empty:
                continue

            useful = [
                column
                for column in (
                    "replay_symbol",
                    "entry_time",
                    "exit_time",
                    "expected_entry_price",
                    "observed_entry_price",
                    "expected_exit_price",
                    "observed_exit_price",
                    "entry_price_relative_error",
                    "exit_price_relative_error",
                    "return_difference_bps",
                    "quantity_integer",
                    "matched",
                )
                if column in frame.columns
            ]
            if not useful:
                continue

            mismatched = frame
            if "matched" in frame.columns:
                mismatched = frame.loc[
                    ~frame["matched"].fillna(False).astype(bool)
                ]
            print(
                mismatched[useful]
                .head(12)
                .to_string(index=False)
            )

    if not summary.empty:
        print("-" * 90)
        print("STRATEGY_SUMMARY")
        columns = [
            column
            for column in (
                "hypothesis_id",
                "strategy",
                "status",
                "missing_engines",
                "non_validating_engines",
                "blockers",
            )
            if column in summary.columns
        ]
        print(summary[columns].to_string(index=False))

    print("BROKER_CALLS 0")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    print("ARTIFACT_ROOT", ART)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
