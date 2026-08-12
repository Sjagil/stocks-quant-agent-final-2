from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RLSuggestion:
    symbol: str
    created_at: datetime
    target_position: float
    confidence: float
    model_id: str
    execution_authority: str = "NONE"


def infer_shadow(model: Any, observation: np.ndarray, *, symbol: str, model_id: str) -> RLSuggestion:
    """Run an RL policy as research/shadow output only."""
    action, _ = model.predict(observation, deterministic=True)
    target = float(np.clip(np.asarray(action).reshape(-1)[0], 0.0, 1.0))
    # SB3 policies do not expose calibrated probability for continuous actions.
    # Keep confidence deliberately conservative until forward calibration exists.
    confidence = float(min(0.50, 0.25 + abs(target - 0.5) * 0.5))
    return RLSuggestion(
        symbol=symbol,
        created_at=datetime.now(timezone.utc),
        target_position=target,
        confidence=confidence,
        model_id=model_id,
        execution_authority="NONE",
    )
