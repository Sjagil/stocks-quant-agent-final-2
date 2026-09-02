from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForwardDistribution:
    mean: float
    uncertainty: float
    q10: float
    q50: float
    q90: float
    expected_cost: float = 0.0
    calibration_confidence: float = 1.0
    stability: float = 1.0
    regime_fit: float = 1.0
    liquidity: float = 1.0

    def __post_init__(self) -> None:
        if self.uncertainty < 0:
            raise ValueError("uncertainty must be non-negative")
        if not self.q10 <= self.q50 <= self.q90:
            raise ValueError("require q10 <= q50 <= q90")
        for name in ("calibration_confidence", "stability", "regime_fit", "liquidity"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")

    def robust_mean(self, uncertainty_penalty: float = 1.0) -> float:
        if uncertainty_penalty < 0:
            raise ValueError("uncertainty_penalty must be non-negative")
        return float(self.mean - uncertainty_penalty * self.uncertainty - self.expected_cost)

    def opportunity_score(self, uncertainty_penalty: float = 1.0, epsilon: float = 1e-9) -> float:
        downside = abs(min(self.q10 - self.expected_cost, 0.0))
        quality = (
            self.calibration_confidence
            * self.stability
            * self.regime_fit
            * self.liquidity
        )
        return float(self.robust_mean(uncertainty_penalty) / (downside + epsilon) * quality)
