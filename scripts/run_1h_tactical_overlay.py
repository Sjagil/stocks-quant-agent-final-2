#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from stocks.research.tactical_overlay import (
    attach_predictions_to_trades,
    fold_overlay_metrics,
    summarize_overlay_folds,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


OVERLAYS = (
    "ALL",
    "PRED_POSITIVE",
    "TOP_HALF",
    "TOP2",
    "TOP1",
    "POSITIVE_TOP2",
)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--variant",
        default="TACTICAL_RAW",
    )

    parser.add_argument(
        "--hold-bars",
        type=int,
        default=21,
    )

    parser.add_argument(
        "--cost-bps-per-side",
        type=float,
        default=10.0,
    )

    args = parser.parse_args()

    predictions_path = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "panel"
        / "panel_oos_predictions.parquet"
    )

    trades_path = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "strategy_factory_1h"
        / "survivor_trades.parquet"
    )

    crosscheck_path = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "pybroker_crosscheck"
        / "summary.csv"
    )

    for path in (
        predictions_path,
        trades_path,
        crosscheck_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(
                path
            )

    predictions = pd.read_parquet(
        predictions_path
    )

    predictions = predictions.loc[
        (
            predictions[
                "variant"
            ]
            == args.variant
        )
        & (
            predictions[
                "hold_bars"
            ]
            == args.hold_bars
        )
    ].copy()

    if predictions.empty:
        raise ValueError(
            "requested tactical "
            "predictions missing"
        )

    trades = pd.read_parquet(
        trades_path
    )

    crosscheck = pd.read_csv(
        crosscheck_path
    )

    eligible = crosscheck.loc[
        crosscheck[
            "execution_contract"
        ]
        == "NEXT_OPEN_REPLAY",
        "hypothesis_id",
    ].astype(str)

    trades = trades.loc[
        trades[
            "hypothesis_id"
        ]
        .astype(str)
        .isin(
            eligible
        )
    ].copy()

    joined = attach_predictions_to_trades(
        trades,
        predictions,
    )

    if joined.empty:
        raise ValueError(
            "no strategy trades matched "
            "OOS tactical predictions"
        )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "tactical_overlay"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    joined.to_parquet(
        output_root
        / "matched_trades.parquet",
        index=False,
    )

    fold_rows = []
    summary_rows = []

    for (
        hypothesis_id,
        hypothesis_trades,
    ) in joined.groupby(
        "hypothesis_id"
    ):
        strategy = str(
            hypothesis_trades[
                "strategy"
            ].iloc[
                0
            ]
        )

        for overlay in OVERLAYS:
            rows = []

            for fold, fold_trades in (
                hypothesis_trades.groupby(
                    "fold"
                )
            ):
                metrics = fold_overlay_metrics(
                    fold_trades,
                    overlay=overlay,
                    cost_bps_per_side=(
                        args
                        .cost_bps_per_side
                    ),
                )

                row = {
                    "hypothesis_id": (
                        hypothesis_id
                    ),
                    "strategy": strategy,
                    "fold": int(
                        fold
                    ),
                    **metrics,
                }

                rows.append(
                    row
                )

                fold_rows.append(
                    row
                )

            summary = (
                summarize_overlay_folds(
                    rows
                )
            )

            summary_rows.append(
                {
                    "hypothesis_id": (
                        hypothesis_id
                    ),
                    "strategy": strategy,
                    "overlay": overlay,
                    **summary,
                }
            )

    fold_frame = pd.DataFrame(
        fold_rows
    )

    summary = pd.DataFrame(
        summary_rows
    )

    baseline = (
        summary.loc[
            summary[
                "overlay"
            ]
            == "ALL",
            [
                "hypothesis_id",
                "median_expectancy_bps",
                "worst_expectancy_bps",
            ],
        ]
        .rename(
            columns={
                "median_expectancy_bps": (
                    "base_median_expectancy_bps"
                ),
                "worst_expectancy_bps": (
                    "base_worst_expectancy_bps"
                ),
            }
        )
    )

    summary = summary.merge(
        baseline,
        on="hypothesis_id",
        how="left",
        validate="many_to_one",
    )

    summary[
        "delta_median_expectancy_bps"
    ] = (
        summary[
            "median_expectancy_bps"
        ]
        - summary[
            "base_median_expectancy_bps"
        ]
    )

    summary[
        "delta_worst_expectancy_bps"
    ] = (
        summary[
            "worst_expectancy_bps"
        ]
        - summary[
            "base_worst_expectancy_bps"
        ]
    )

    summary[
        "status"
    ] = "REJECT"

    promote = (
        (
            summary[
                "overlay"
            ]
            != "ALL"
        )
        & (
            summary[
                "usable_folds"
            ]
            >= 3
        )
        & (
            summary[
                "positive_fold_ratio"
            ]
            >= 0.75
        )
        & (
            summary[
                "median_expectancy_bps"
            ]
            > 0
        )
        & (
            summary[
                "worst_expectancy_bps"
            ]
            > 0
        )
        & (
            summary[
                "delta_median_expectancy_bps"
            ]
            > 0
        )
        & (
            summary[
                "delta_worst_expectancy_bps"
            ]
            >= 0
        )
        & (
            summary[
                "median_retention_ratio"
            ]
            >= 0.25
        )
    )

    summary.loc[
        promote,
        "status",
    ] = (
        "TACTICAL_OVERLAY_SURVIVOR"
    )

    summary.loc[
        summary[
            "overlay"
        ]
        == "ALL",
        "status",
    ] = "BASELINE"

    fold_frame.to_csv(
        output_root
        / "fold_results.csv",
        index=False,
    )

    summary.to_csv(
        output_root
        / "summary.csv",
        index=False,
    )

    audit = {
        "schema": (
            "one_hour_tactical_overlay_v1"
        ),
        "primary_timeframe": "1h",
        "tactical_context": "15m",
        "panel_variant": (
            args.variant
        ),
        "panel_hold_bars": (
            args.hold_bars
        ),
        "matched_trades": int(
            len(
                joined
            )
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }

    (
        output_root
        / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        summary.sort_values(
            [
                "status",
                "median_expectancy_bps",
            ],
            ascending=[
                True,
                False,
            ],
        ).to_string(
            index=False
        )
    )

    print()
    print(
        "ARTIFACT_ROOT",
        output_root,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
