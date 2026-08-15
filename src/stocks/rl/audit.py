from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FoldAudit:
    fold: int
    selected_seed: int

    rl_return: float
    rl_sharpe: float
    rl_drawdown: float
    rl_trades: int

    buy_hold_return: float
    buy_hold_sharpe: float
    buy_hold_drawdown: float

    excess_return_vs_buy_hold: float
    sharpe_delta_vs_buy_hold: float

    beats_cash: bool
    beats_buy_hold_return: bool
    beats_buy_hold_sharpe: bool


@dataclass(frozen=True)
class ExperimentAudit:
    algorithm: str
    symbol: str
    timeframe: str

    fold_count: int

    median_rl_return: float
    median_rl_sharpe: float
    worst_rl_drawdown: float

    median_buy_hold_return: float
    median_buy_hold_sharpe: float

    positive_fold_ratio: float
    beat_buy_hold_return_ratio: float
    beat_buy_hold_sharpe_ratio: float

    drawdown_gate: bool
    positive_net_gate: bool
    stability_gate: bool

    promotion_candidate: bool

    folds: tuple[FoldAudit, ...]

    execution_authority: str = "NONE"


def audit_experiment(
    path: str | Path,
    *,
    maximum_drawdown: float = 0.15,
) -> ExperimentAudit:
    source = Path(path)

    data = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    rows: list[FoldAudit] = []

    for fold in data["folds"]:
        rl = fold["selected_test"]
        bh = fold["buy_hold_test"]

        rl_return = float(
            rl["total_return"]
        )

        rl_sharpe = float(
            rl["sharpe"]
        )

        rl_dd = float(
            rl["max_drawdown"]
        )

        bh_return = float(
            bh["total_return"]
        )

        bh_sharpe = float(
            bh["sharpe"]
        )

        rows.append(
            FoldAudit(
                fold=int(
                    fold["fold"]
                ),
                selected_seed=int(
                    fold["selected_seed"]
                ),
                rl_return=rl_return,
                rl_sharpe=rl_sharpe,
                rl_drawdown=rl_dd,
                rl_trades=int(
                    rl.get(
                        "trades",
                        0,
                    )
                ),
                buy_hold_return=(
                    bh_return
                ),
                buy_hold_sharpe=(
                    bh_sharpe
                ),
                buy_hold_drawdown=float(
                    bh["max_drawdown"]
                ),
                excess_return_vs_buy_hold=(
                    rl_return
                    - bh_return
                ),
                sharpe_delta_vs_buy_hold=(
                    rl_sharpe
                    - bh_sharpe
                ),
                beats_cash=(
                    rl_return > 0
                ),
                beats_buy_hold_return=(
                    rl_return
                    > bh_return
                ),
                beats_buy_hold_sharpe=(
                    rl_sharpe
                    > bh_sharpe
                ),
            )
        )

    if not rows:
        raise ValueError(
            "experiment has no folds"
        )

    positive_fold_ratio = (
        sum(
            row.beats_cash
            for row in rows
        )
        / len(rows)
    )

    beat_return_ratio = (
        sum(
            row.beats_buy_hold_return
            for row in rows
        )
        / len(rows)
    )

    beat_sharpe_ratio = (
        sum(
            row.beats_buy_hold_sharpe
            for row in rows
        )
        / len(rows)
    )

    median_return = (
        statistics.median(
            row.rl_return
            for row in rows
        )
    )

    median_sharpe = (
        statistics.median(
            row.rl_sharpe
            for row in rows
        )
    )

    worst_dd = max(
        row.rl_drawdown
        for row in rows
    )

    drawdown_gate = (
        worst_dd
        <= maximum_drawdown
    )

    positive_net_gate = (
        median_return > 0
        and positive_fold_ratio >= 0.5
    )

    stability_gate = (
        median_sharpe > 0
        and positive_fold_ratio >= 0.5
    )

    return ExperimentAudit(
        algorithm=str(
            data["algorithm"]
        ),
        symbol=str(
            data["symbol"]
        ),
        timeframe=str(
            data["timeframe"]
        ),
        fold_count=len(
            rows
        ),
        median_rl_return=(
            median_return
        ),
        median_rl_sharpe=(
            median_sharpe
        ),
        worst_rl_drawdown=(
            worst_dd
        ),
        median_buy_hold_return=(
            statistics.median(
                row.buy_hold_return
                for row in rows
            )
        ),
        median_buy_hold_sharpe=(
            statistics.median(
                row.buy_hold_sharpe
                for row in rows
            )
        ),
        positive_fold_ratio=(
            positive_fold_ratio
        ),
        beat_buy_hold_return_ratio=(
            beat_return_ratio
        ),
        beat_buy_hold_sharpe_ratio=(
            beat_sharpe_ratio
        ),
        drawdown_gate=(
            drawdown_gate
        ),
        positive_net_gate=(
            positive_net_gate
        ),
        stability_gate=(
            stability_gate
        ),
        promotion_candidate=(
            drawdown_gate
            and positive_net_gate
            and stability_gate
        ),
        folds=tuple(
            rows
        ),
    )


def audit_to_dict(
    audit: ExperimentAudit,
) -> dict[str, Any]:
    return asdict(
        audit
    )
