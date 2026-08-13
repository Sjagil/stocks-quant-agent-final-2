from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PromotionDecision:
    algorithm: str
    symbol: str
    timeframe: str

    absolute_edge_gate: bool
    benchmark_edge_gate: bool
    drawdown_gate: bool

    profit_factor_gate: bool | None
    forward_episode_gate: bool
    regime_gate: bool

    research_candidate: bool
    promotion_ready: bool

    reasons: tuple[str, ...]

    execution_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_promotion(
    row: dict[str, Any],
    promotion: dict[str, Any],
    *,
    closed_forward_episodes: int = 0,
    regime_robust: bool = False,
) -> PromotionDecision:
    max_drawdown = float(
        promotion.get(
            "maximum_oos_drawdown",
            0.15,
        )
    )

    min_forward = int(
        promotion.get(
            "minimum_closed_forward_episodes",
            500,
        )
    )

    minimum_pf = float(
        promotion.get(
            "minimum_oos_profit_factor",
            1.15,
        )
    )

    median_return = float(
        row.get(
            "median_rl_return",
            0.0,
        )
    )

    median_sharpe = float(
        row.get(
            "median_rl_sharpe",
            0.0,
        )
    )

    worst_drawdown = float(
        row.get(
            "worst_rl_drawdown",
            1.0,
        )
    )

    positive_fold_ratio = float(
        row.get(
            "positive_fold_ratio",
            0.0,
        )
    )

    beat_return_ratio = float(
        row.get(
            "beat_buy_hold_return_ratio",
            0.0,
        )
    )

    beat_sharpe_ratio = float(
        row.get(
            "beat_buy_hold_sharpe_ratio",
            0.0,
        )
    )

    absolute_edge_gate = (
        median_return > 0
        and median_sharpe > 0
        and positive_fold_ratio >= 0.50
    )

    benchmark_edge_gate = (
        beat_return_ratio >= 0.50
        or beat_sharpe_ratio >= 0.50
    )

    drawdown_gate = (
        worst_drawdown
        <= max_drawdown
    )

    profit_factor = row.get(
        "median_profit_factor"
    )

    if profit_factor is None:
        profit_factor_gate = None
    else:
        profit_factor_gate = (
            float(profit_factor)
            >= minimum_pf
        )

    forward_episode_gate = (
        int(
            closed_forward_episodes
        )
        >= min_forward
    )

    regime_gate = bool(
        regime_robust
    )

    research_candidate = (
        absolute_edge_gate
        and benchmark_edge_gate
        and drawdown_gate
    )

    promotion_ready = (
        research_candidate
        and profit_factor_gate is True
        and forward_episode_gate
        and regime_gate
    )

    reasons: list[str] = []

    if not absolute_edge_gate:
        reasons.append(
            "ABSOLUTE_EDGE_NOT_PROVEN"
        )

    if not benchmark_edge_gate:
        reasons.append(
            "NO_OOS_BENCHMARK_EDGE"
        )

    if not drawdown_gate:
        reasons.append(
            "MAX_DRAWDOWN_GATE_FAILED"
        )

    if profit_factor_gate is None:
        reasons.append(
            "PROFIT_FACTOR_NOT_YET_IN_EXPERIMENT_ARTIFACT"
        )
    elif not profit_factor_gate:
        reasons.append(
            "PROFIT_FACTOR_GATE_FAILED"
        )

    if not forward_episode_gate:
        reasons.append(
            "INSUFFICIENT_FORWARD_EPISODES"
        )

    if not regime_gate:
        reasons.append(
            "REGIME_ROBUSTNESS_NOT_PROVEN"
        )

    return PromotionDecision(
        algorithm=str(
            row.get(
                "algorithm",
                "",
            )
        ),
        symbol=str(
            row.get(
                "symbol",
                "",
            )
        ),
        timeframe=str(
            row.get(
                "timeframe",
                "",
            )
        ),
        absolute_edge_gate=(
            absolute_edge_gate
        ),
        benchmark_edge_gate=(
            benchmark_edge_gate
        ),
        drawdown_gate=(
            drawdown_gate
        ),
        profit_factor_gate=(
            profit_factor_gate
        ),
        forward_episode_gate=(
            forward_episode_gate
        ),
        regime_gate=(
            regime_gate
        ),
        research_candidate=(
            research_candidate
        ),
        promotion_ready=(
            promotion_ready
        ),
        reasons=tuple(
            reasons
        ),
    )
