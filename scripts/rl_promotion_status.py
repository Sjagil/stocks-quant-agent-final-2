from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.rl.config import (
    load_rl_yaml,
)
from stocks.rl.promotion import (
    evaluate_promotion,
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
        "--timeframe",
        default="1h",
    )

    parser.add_argument(
        "--closed-forward-episodes",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--regime-robust",
        action="store_true",
    )

    args = parser.parse_args()

    path = (
        ROOT
        / "artifacts"
        / "rl"
        / "audits"
        / (
            f"{args.algorithm}-"
            f"{args.timeframe}.json"
        )
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    _, _, _, promotion = (
        load_rl_yaml(
            ROOT / "config/rl.yaml"
        )
    )

    results = []

    for row in data[
        "results"
    ]:
        decision = evaluate_promotion(
            row,
            promotion,
            closed_forward_episodes=(
                args.closed_forward_episodes
            ),
            regime_robust=(
                args.regime_robust
            ),
        )

        results.append(
            decision.to_dict()
        )

        print()
        print(
            decision.symbol,
            decision.algorithm,
        )

        print(
            "RESEARCH_CANDIDATE",
            decision.research_candidate,
        )

        print(
            "PROMOTION_READY",
            decision.promotion_ready,
        )

        print(
            "REASONS",
            ",".join(
                decision.reasons
            ),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
