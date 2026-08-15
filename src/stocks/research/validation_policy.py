from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class GeneralizationDecision:
    status: str
    passed: bool
    evaluable: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "evaluable": self.evaluable,
            "reasons": list(self.reasons),
        }


def classify_generalization(
    *,
    unseen_symbols_available: int,
    unseen_symbols_traded: int,
    oos_trades: int,
    positive_fold_ratio: float,
    stress_positive_fold_ratio: float,
    median_expectancy_bps: float,
    median_stress_expectancy_bps: float,
    positive_symbol_ratio: float,
    stress_positive_symbol_ratio: float,
    max_symbol_trade_share: float,
    policy: Mapping[str, Any],
) -> GeneralizationDecision:
    minimum_available = int(policy["min_unseen_symbols_available"])
    minimum_traded = int(policy["min_unseen_symbols_traded"])
    minimum_trades = int(policy["min_oos_trades"])

    if unseen_symbols_available < minimum_available:
        return GeneralizationDecision(
            "NOT_EVALUABLE_INSUFFICIENT_UNSEEN_1H",
            False,
            False,
            (f"unseen_symbols_available<{minimum_available}",),
        )

    if unseen_symbols_traded < minimum_traded:
        return GeneralizationDecision(
            "NOT_EVALUABLE_INSUFFICIENT_UNSEEN_TRADES",
            False,
            False,
            (f"unseen_symbols_traded<{minimum_traded}",),
        )

    if oos_trades < minimum_trades:
        return GeneralizationDecision(
            "NOT_EVALUABLE_INSUFFICIENT_OOS_TRADES",
            False,
            False,
            (f"oos_trades<{minimum_trades}",),
        )

    failures: list[str] = []
    if positive_fold_ratio < float(policy["min_positive_fold_ratio"]):
        failures.append("positive_fold_ratio")
    if stress_positive_fold_ratio < float(policy["min_stress_positive_fold_ratio"]):
        failures.append("stress_positive_fold_ratio")
    if positive_symbol_ratio < float(policy["min_positive_symbol_ratio"]):
        failures.append("positive_symbol_ratio")
    if stress_positive_symbol_ratio < float(policy["min_stress_positive_symbol_ratio"]):
        failures.append("stress_positive_symbol_ratio")
    if max_symbol_trade_share > float(policy["max_symbol_trade_share"]):
        failures.append("max_symbol_trade_share")
    if bool(policy.get("require_positive_median_expectancy", True)) and median_expectancy_bps <= 0:
        failures.append("median_expectancy_bps")
    if bool(policy.get("require_positive_median_stress_expectancy", True)) and median_stress_expectancy_bps <= 0:
        failures.append("median_stress_expectancy_bps")

    if failures:
        return GeneralizationDecision(
            "DYNAMIC_UNIVERSE_REJECT",
            False,
            True,
            tuple(failures),
        )

    return GeneralizationDecision(
        "DYNAMIC_UNIVERSE_VALIDATED",
        True,
        True,
        (),
    )


def promotion_from_evidence(
    *,
    existing_stage: str,
    crosscheck_status: str | None,
    generalization_status: str | None,
) -> str:
    existing = str(existing_stage or "")
    if existing in {"FINALIST_CANDIDATE", "CHALLENGER"}:
        return existing

    crosscheck = str(crosscheck_status or "")
    generalization = str(generalization_status or "")

    if generalization == "DYNAMIC_UNIVERSE_REJECT":
        return "REJECTED_AFTER_GENERALIZATION"

    if (
        crosscheck == "CROSS_ENGINE_VALIDATED"
        and generalization == "DYNAMIC_UNIVERSE_VALIDATED"
    ):
        return "FINALIST_CANDIDATE"

    if crosscheck == "CROSS_ENGINE_VALIDATED":
        return "GENERALIZATION_QUEUE"

    if crosscheck == "CROSS_ENGINE_PROVISIONAL":
        return "VALIDATION_QUEUE"

    if crosscheck == "CROSS_ENGINE_REJECT":
        return "REJECTED_AFTER_CROSSCHECK"

    return "VALIDATION_QUEUE"
