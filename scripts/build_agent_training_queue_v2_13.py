#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from stocks.agents.candle_fabric import frame_for_timeframe


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--include-data-incomplete",
        action="store_true",
    )
    args = parser.parse_args()

    forward_path = (
        ROOT
        / "artifacts/research_runtime/"
        "forward_signal_state/signals.csv"
    )
    shariah_path = (
        ROOT
        / "artifacts/research_runtime/"
        "shariah_financial_verification/verification.csv"
    )
    roster_path = (
        ROOT
        / "artifacts/research_runtime/"
        "final_strategy_roster/roster.csv"
    )

    if not forward_path.is_file():
        raise SystemExit("forward signal state missing")
    if not roster_path.is_file():
        raise SystemExit("final strategy roster missing")

    forward = pd.read_csv(forward_path)
    roster = pd.read_csv(roster_path)

    validated_ids = set(
        roster.loc[
            roster["roster_status"].astype(str)
            == "BROADLY_VALIDATED_FINALIST",
            "hypothesis_id",
        ].astype(str)
    )

    forward["hypothesis_id"] = (
        forward["hypothesis_id"].astype(str)
    )
    forward = forward.loc[
        forward["hypothesis_id"].isin(
            validated_ids
        )
    ].copy()

    if shariah_path.is_file():
        shariah = pd.read_csv(shariah_path)
        keep = [
            "symbol",
            "status",
            "financial_ratio_status",
            "trade_eligible",
        ]
        shariah = shariah[
            [column for column in keep if column in shariah.columns]
        ].drop_duplicates("symbol")
        forward = forward.merge(
            shariah,
            on="symbol",
            how="left",
        )
    else:
        forward["status"] = "SHARIAH_UNKNOWN"
        forward["financial_ratio_status"] = "UNKNOWN"
        forward["trade_eligible"] = False

    grouped = []
    for symbol, rows in forward.groupby("symbol"):
        status = str(
            rows["status"].iloc[0]
            if "status" in rows
            else "UNKNOWN"
        )
        ratio_status = str(
            rows["financial_ratio_status"].iloc[0]
            if "financial_ratio_status" in rows
            else "UNKNOWN"
        )

        if "INELIGIBLE" in status or ratio_status == "FAIL":
            continue

        if (
            ratio_status != "PASS"
            and not args.include_data_incomplete
        ):
            continue

        try:
            frame = frame_for_timeframe(
                ROOT,
                str(symbol),
                args.timeframe,
            )
            candle_rows = len(frame)
            candle_ready = candle_rows >= 2500
        except Exception:
            candle_rows = 0
            candle_ready = False

        if not candle_ready:
            continue

        grouped.append(
            {
                "symbol": str(symbol).upper(),
                "timeframe": args.timeframe,
                "validated_strategy_count": int(
                    rows["hypothesis_id"].nunique()
                ),
                "max_applicability_score": float(
                    pd.to_numeric(
                        rows["applicability_score"],
                        errors="coerce",
                    ).max()
                ),
                "shariah_status": status,
                "financial_ratio_status": ratio_status,
                "candle_rows": int(candle_rows),
                "research_only": True,
                "execution_authority": "NONE",
            }
        )

    result = pd.DataFrame(grouped)

    if not result.empty:
        result = (
            result.sort_values(
                [
                    "validated_strategy_count",
                    "max_applicability_score",
                    "candle_rows",
                ],
                ascending=[False, False, False],
            )
            .head(max(1, int(args.limit)))
            .reset_index(drop=True)
        )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "agent_training_queue_v2_13"
    )
    output.mkdir(parents=True, exist_ok=True)
    result.to_csv(output / "queue.csv", index=False)

    print(
        "AGENT_TRAINING_QUEUE_V2_13",
        "ROWS",
        len(result),
        "TIMEFRAME",
        args.timeframe,
    )
    if not result.empty:
        print(result.to_string(index=False))
    print("RESEARCH_ONLY True")
    print("EXECUTION_AUTHORITY NONE")
    print("OUTPUT", output / "queue.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
