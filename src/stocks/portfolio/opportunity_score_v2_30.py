from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpportunityInputs:
    robust_expected_return: float
    q10: float
    expected_cost: float
    calibration_confidence: float
    stability: float
    regime_fit: float
    liquidity: float

    def __post_init__(self) -> None:
        for field in ("calibration_confidence", "stability", "regime_fit", "liquidity"):
            value = float(getattr(self, field))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be in [0,1]")


def opportunity_score(inputs: OpportunityInputs, *, epsilon: float = 1e-9) -> float:
    net_mean = float(inputs.robust_expected_return) - float(inputs.expected_cost)
    net_q10 = float(inputs.q10) - float(inputs.expected_cost)
    downside = abs(min(net_q10, 0.0))
    quality = (
        inputs.calibration_confidence
        * inputs.stability
        * inputs.regime_fit
        * inputs.liquidity
    )
    return float(net_mean / (downside + epsilon) * quality)
