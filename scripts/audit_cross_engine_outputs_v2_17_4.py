#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ART = (
    ROOT
    / "artifacts/research_runtime/"
    "cross_engine_strategy_validation_v2_17"
)


def parse_value(value):
    if isinstance(value, (list, dict, tuple)):
        return value
    if value is None or (
        isinstance(value, float) and pd.isna(value)
    ):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def safe_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None


def main() -> int:
    engine_path = ART / "engine_results.csv"
    summary_path = ART / "strategy_summary.csv"
    if not engine_path.is_file():
        raise SystemExit(f"missing {engine_path}")

    engines = pd.read_csv(engine_path)
    summary = safe_csv(summary_path)
    if summary is None:
        summary = pd.DataFrame()

    print("=" * 100)
    print("CROSS_ENGINE_PARITY_DEEP_AUDIT_V2_17_5")

    metric_columns = (
        "expected_trades",
        "observed_trades",
        "trade_count_match",
        "exact_symbols",
        "exact_timestamps",
        "integer_quantity",
        "maximum_fill_price_relative_error",
        "maximum_trade_return_difference_bps",
        "trade_match_ratio",
    )

    for row in engines.to_dict(orient="records"):
        engine = str(row.get("engine") or "")
        print("-" * 100)
        print(
            "ENGINE",
            engine,
            "MODE",
            row.get("mode"),
            "PARITY",
            row.get("parity"),
            "TRADES",
            row.get("trades"),
        )

        for column in metric_columns:
            if column in row and pd.notna(row[column]):
                print(" ", column.upper(), row[column])

        error = parse_value(row.get("error"))
        warnings = parse_value(row.get("warnings"))
        if error:
            print("  ERROR", error)
        if warnings:
            print("  WARNINGS", warnings)

        parity_files = sorted(
            path
            for path in ART.rglob(f"{engine}_parity_rows.csv")
            if path.is_file()
        )
        for parity_path in parity_files:
            frame = safe_csv(parity_path)
            relative = parity_path.relative_to(ART)
            if frame is None:
                print("  PARITY_FILE", relative, "EMPTY")
                continue

            print(
                "  PARITY_FILE",
                relative,
                "ROWS",
                len(frame),
            )
            if frame.empty:
                continue

            mismatch_col = (
                "row_match"
                if "row_match" in frame.columns
                else "matched"
                if "matched" in frame.columns
                else None
            )
            mismatched = frame
            if mismatch_col is not None:
                mask = (
                    frame[mismatch_col]
                    .fillna(False)
                    .astype(bool)
                )
                mismatched = frame.loc[~mask].copy()

            print("  MISMATCH_ROWS", len(mismatched))
            useful = [
                column
                for column in (
                    "row",
                    "expected_symbol",
                    "observed_symbol",
                    "symbol_match",
                    "entry_time_match",
                    "exit_time_match",
                    "entry_price_relative_error",
                    "exit_price_relative_error",
                    "return_difference_bps",
                    "integer_quantity",
                    "row_match",
                )
                if column in mismatched.columns
            ]
            if useful and not mismatched.empty:
                print(
                    mismatched[useful]
                    .head(20)
                    .to_string(index=False)
                )

    if not summary.empty:
        print("=" * 100)
        print("STRATEGY_SUMMARY")
        columns = [
            column
            for column in (
                "hypothesis_id",
                "strategy",
                "status",
                "missing_engines",
                "non_validating_engines",
                "engine_failures",
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
