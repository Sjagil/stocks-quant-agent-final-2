from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.research.mtf_features import (
    build_causal_mtf_dataset,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbols",
        required=True,
    )

    args = parser.parse_args()

    results = []

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "mtf"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for symbol in (
        value.strip().upper()
        for value
        in args.symbols.split(",")
        if value.strip()
    ):
        dataset = (
            build_causal_mtf_dataset(
                ROOT,
                symbol,
            )
        )

        frame = dataset.frame

        output = (
            output_root
            / f"{symbol}_mtf.parquet"
        )

        frame.to_parquet(
            output,
            index=False,
        )

        feature_columns = [
            column
            for column in frame.columns
            if any(
                column.startswith(
                    f"{tf}_"
                )
                for tf in (
                    "15m",
                    "2h",
                    "4h",
                    "1d",
                    "1w",
                )
            )
            and not (
                column.endswith(
                    "_bar_time"
                )
                or column.endswith(
                    "_availability_time"
                )
            )
        ]

        future_violations = 0

        for timeframe in (
            dataset.available_timeframes
        ):
            column = (
                f"{timeframe}_"
                "availability_time"
            )

            future_violations += int(
                (
                    frame[column].notna()
                    &
                    (
                        frame[column]
                        >
                        frame[
                            "decision_time"
                        ]
                    )
                ).sum()
            )

        result = {
            "symbol": symbol,
            "rows": len(frame),
            "feature_columns": len(
                feature_columns
            ),
            "available_context": list(
                dataset
                .available_timeframes
            ),
            "missing_context": list(
                dataset
                .missing_timeframes
            ),
            "future_violations": (
                future_violations
            ),
            "first_decision": (
                str(
                    frame[
                        "decision_time"
                    ].min()
                )
            ),
            "last_decision": (
                str(
                    frame[
                        "decision_time"
                    ].max()
                )
            ),
            "output": str(
                output
            ),
        }

        results.append(
            result
        )

        print()
        print(
            symbol,
        )
        print(
            "ROWS",
            result["rows"],
        )
        print(
            "FEATURES",
            result[
                "feature_columns"
            ],
        )
        print(
            "AVAILABLE",
            ",".join(
                result[
                    "available_context"
                ]
            ),
        )
        print(
            "MISSING",
            ",".join(
                result[
                    "missing_context"
                ]
            )
            or "NONE",
        )
        print(
            "FUTURE_VIOLATIONS",
            future_violations,
        )

    artifact = (
        output_root
        / "audit.json"
    )

    artifact.write_text(
        json.dumps(
            {
                "schema": (
                    "causal_mtf_dataset_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "ARTIFACT",
        artifact,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
