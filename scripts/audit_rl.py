from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.rl.audit import (
    audit_experiment,
    audit_to_dict,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--algorithm",
        choices=[
            "PPO",
            "SAC",
        ],
        required=True,
    )

    parser.add_argument(
        "--symbols",
        default=(
            "SPY,QQQ,AAPL,AMD,NVDA"
        ),
    )

    parser.add_argument(
        "--timeframe",
        default="1h",
    )

    parser.add_argument(
        "--max-drawdown",
        type=float,
        default=0.15,
    )

    args = parser.parse_args()

    results = []

    for symbol in (
        value.strip().upper()
        for value
        in args.symbols.split(",")
        if value.strip()
    ):
        path = (
            ROOT
            / "artifacts"
            / "rl"
            / "walk_forward"
            / args.algorithm
            / symbol
            / args.timeframe
            / "experiment.json"
        )

        if not path.is_file():
            print(
                symbol,
                "MISSING"
            )
            continue

        audit = audit_experiment(
            path,
            maximum_drawdown=(
                args.max_drawdown
            ),
        )

        payload = audit_to_dict(
            audit
        )

        results.append(
            payload
        )

        print()
        print(
            symbol,
            args.algorithm,
        )

        print(
            "RL_RETURN",
            round(
                audit.median_rl_return,
                6,
            ),
        )

        print(
            "RL_SHARPE",
            round(
                audit.median_rl_sharpe,
                4,
            ),
        )

        print(
            "WORST_DD",
            round(
                audit.worst_rl_drawdown,
                4,
            ),
        )

        print(
            "BEATS_BH_RETURN",
            audit.beat_buy_hold_return_ratio,
        )

        print(
            "BEATS_BH_SHARPE",
            audit.beat_buy_hold_sharpe_ratio,
        )

        print(
            "PROMOTION_CANDIDATE",
            audit.promotion_candidate,
        )

    output = (
        ROOT
        / "artifacts"
        / "rl"
        / "audits"
        / (
            args.algorithm
            + "-"
            + args.timeframe
            + ".json"
        )
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            {
                "schema": (
                    "rl_audit_v1"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "ARTIFACT",
        output
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
