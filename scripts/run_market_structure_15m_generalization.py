
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stocks.research.market_structure_15m_generalization import (
    build_market_structure_15m_generalization,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    (
        summary,
        missing,
        trades,
        audit,
    ) = build_market_structure_15m_generalization(
        ROOT
    )

    output = (
        ROOT
        / "artifacts/research_runtime/"
        "market_structure_15m_generalization"
    )
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        output / "symbol_summary.csv",
        index=False,
    )
    missing.to_csv(
        output / "hydration_queue.csv",
        index=False,
    )
    trades.to_parquet(
        output / "resolved_trades.parquet",
        index=False,
    )

    (
        output / "audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "MARKET_STRUCTURE_15M_GENERALIZATION_V2_7",
        "STATUS",
        audit["status"],
        "ELIGIBLE",
        audit["eligible_symbols"],
        "TRADED",
        audit["traded_symbols"],
        "OOS_TRADES",
        audit["oos_trades"],
    )

    if not summary.empty:
        print(
            summary.to_string(
                index=False
            )
        )

    if not missing.empty:
        print(
            "15M_HYDRATION_REQUIRED",
            len(missing),
        )
        print(
            missing.to_string(
                index=False
            )
        )

    print(
        "ARTIFACT_ROOT",
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
