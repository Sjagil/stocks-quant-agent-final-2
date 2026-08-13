from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def classify(
    *,
    variant: str,
    median_ic: float,
    worst_ic: float,
    positive_ratio: float,
    median_spread: float,
    delta_median: float,
    delta_worst: float,
) -> str:
    robust = (
        median_ic > 0.0
        and worst_ic > 0.0
        and positive_ratio >= 0.999
        and median_spread > 0.0
    )

    if variant == "BASE":
        return (
            "BASE_SURVIVOR"
            if robust
            else "BASE_REJECT"
        )

    if (
        robust
        and delta_median > 0.0
        and delta_worst >= 0.0
    ):
        return "PROMOTE_CONTEXT"

    if robust:
        return (
            "ROBUST_NO_BASE_IMPROVEMENT"
        )

    if (
        median_ic > 0.0
        and positive_ratio
        >= (2.0 / 3.0)
        and median_spread > 0.0
    ):
        return (
            "UNSTABLE_CHALLENGER"
        )

    return "REJECT"


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    cases = {}

    for path in args.inputs:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if (
            payload.get(
                "execution_authority"
            )
            != "NONE"
        ):
            raise ValueError(
                f"{path}: unexpected "
                "execution authority"
            )

        for result in payload.get(
            "results",
            []
        ):
            key = (
                str(
                    result["symbol"]
                ).upper(),
                int(
                    result["hold_bars"]
                ),
            )

            cases[
                key
            ] = result

    rows = []

    for (
        symbol,
        hold_bars,
    ), result in sorted(
        cases.items()
    ):
        variants = result[
            "variants"
        ]

        base = next(
            variant
            for variant
            in variants
            if variant[
                "variant"
            ]
            == "BASE"
        )

        base_median = float(
            base[
                "median_spearman_ic"
            ]
        )

        base_worst = float(
            base[
                "worst_spearman_ic"
            ]
        )

        for variant in variants:
            median_ic = float(
                variant[
                    "median_spearman_ic"
                ]
            )

            worst_ic = float(
                variant[
                    "worst_spearman_ic"
                ]
            )

            positive_ratio = float(
                variant[
                    "positive_spearman_ratio"
                ]
            )

            median_spread = float(
                variant[
                    "median_top_bottom_spread"
                ]
            )

            delta_median = (
                median_ic
                - base_median
            )

            delta_worst = (
                worst_ic
                - base_worst
            )

            status = classify(
                variant=variant[
                    "variant"
                ],
                median_ic=median_ic,
                worst_ic=worst_ic,
                positive_ratio=(
                    positive_ratio
                ),
                median_spread=(
                    median_spread
                ),
                delta_median=(
                    delta_median
                ),
                delta_worst=(
                    delta_worst
                ),
            )

            rows.append(
                {
                    "symbol": symbol,
                    "hold_bars": (
                        hold_bars
                    ),
                    "variant": (
                        variant[
                            "variant"
                        ]
                    ),
                    "status": status,
                    "fold_count": (
                        variant[
                            "fold_count"
                        ]
                    ),
                    "median_spearman_ic": (
                        median_ic
                    ),
                    "worst_spearman_ic": (
                        worst_ic
                    ),
                    "positive_spearman_ratio": (
                        positive_ratio
                    ),
                    "median_top_bottom_spread": (
                        median_spread
                    ),
                    "median_pearson_ic": (
                        variant.get(
                            "median_pearson_ic"
                        )
                    ),
                    "delta_median_vs_base": (
                        delta_median
                    ),
                    "delta_worst_vs_base": (
                        delta_worst
                    ),
                    "common_rows": (
                        variant[
                            "common_rows"
                        ]
                    ),
                }
            )

    frame = pd.DataFrame(
        rows
    )

    order = {
        "PROMOTE_CONTEXT": 0,
        "BASE_SURVIVOR": 1,
        "ROBUST_NO_BASE_IMPROVEMENT": 2,
        "UNSTABLE_CHALLENGER": 3,
        "BASE_REJECT": 4,
        "REJECT": 5,
    }

    frame[
        "_order"
    ] = frame[
        "status"
    ].map(
        order
    )

    frame = (
        frame.sort_values(
            [
                "_order",
                "median_spearman_ic",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop(
            columns=[
                "_order",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
    )

    csv_path = (
        output_root
        / "mtf_promotion_matrix.csv"
    )

    json_path = (
        output_root
        / "mtf_promotion_matrix.json"
    )

    frame.to_csv(
        csv_path,
        index=False,
    )

    json_path.write_text(
        json.dumps(
            {
                "schema": (
                    "mtf_promotion_matrix_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "rows": (
                    frame.to_dict(
                        orient="records"
                    )
                ),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        frame[
            [
                "symbol",
                "hold_bars",
                "variant",
                "status",
                "median_spearman_ic",
                "worst_spearman_ic",
                "positive_spearman_ratio",
                "median_top_bottom_spread",
                "delta_median_vs_base",
                "delta_worst_vs_base",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "CSV",
        csv_path,
    )

    print(
        "JSON",
        json_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
