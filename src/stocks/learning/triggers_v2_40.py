from __future__ import annotations

from datetime import datetime, timezone

from .contracts_v2_40 import RetrainDecisionV240


def _age_hours(value: str | None) -> float | None:
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)


def decide_retrain_v240(
    *,
    current_rows: int,
    previous_rows: int,
    last_success_at: str | None,
    last_attempt_at: str | None = None,
    shadow_outcomes_since_train: int = 0,
    drift_severity: float,
    policy: dict,
    force: bool = False,
) -> RetrainDecisionV240:
    new_rows = max(0, int(current_rows) - int(previous_rows))
    model_age = _age_hours(last_success_at)
    attempt_age = _age_hours(last_attempt_at)
    reasons: list[str] = []
    blockers: list[str] = []

    min_rows = int(policy.get("minimum_rows", 800))
    min_new = int(policy.get("minimum_new_rows", 32))
    min_shadow = int(policy.get("minimum_shadow_outcomes", 30))
    drift_threshold = float(policy.get("drift_retrain_threshold", 0.10))
    max_age = float(policy.get("maximum_model_age_hours", 72))
    cooldown = float(policy.get("minimum_retrain_cooldown_hours", 6))
    require_new = bool(policy.get("require_new_data", True))

    if int(current_rows) < min_rows:
        blockers.append("INSUFFICIENT_DATA_ROWS")

    if force:
        reasons.append("FORCED_RETRAIN")
    if new_rows >= min_new:
        reasons.append("NEW_DATA_THRESHOLD")
    if int(shadow_outcomes_since_train) >= min_shadow:
        reasons.append("SHADOW_OUTCOME_THRESHOLD")
    if float(drift_severity) >= drift_threshold:
        reasons.append("DRIFT_THRESHOLD")
    if model_age is None:
        reasons.append("NO_EXISTING_MODEL")
    elif model_age >= max_age:
        reasons.append("MODEL_AGE_THRESHOLD")

    if last_attempt_at and attempt_age is not None and attempt_age < cooldown and not force:
        blockers.append("RETRAIN_COOLDOWN")

    if require_new and not force and last_success_at and new_rows <= 0 and not any(
        r in reasons for r in ("SHADOW_OUTCOME_THRESHOLD", "DRIFT_THRESHOLD", "MODEL_AGE_THRESHOLD")
    ):
        blockers.append("NO_NEW_INFORMATION")

    should = bool(reasons) and not blockers
    return RetrainDecisionV240(
        should_train=should,
        reasons=tuple(dict.fromkeys(reasons)),
        blockers=tuple(dict.fromkeys(blockers)),
        new_rows=new_rows,
        shadow_outcomes=int(shadow_outcomes_since_train),
        drift_severity=float(drift_severity),
        model_age_hours=model_age,
    )


__all__ = ["decide_retrain_v240"]
