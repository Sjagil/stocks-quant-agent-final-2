from stocks.learning.triggers_v2_40 import decide_retrain_v240


def policy():
    return {
        "minimum_rows": 800,
        "minimum_new_rows": 32,
        "minimum_shadow_outcomes": 30,
        "drift_retrain_threshold": 0.10,
        "maximum_model_age_hours": 72,
        "minimum_retrain_cooldown_hours": 0,
        "require_new_data": True,
    }


def test_new_data_triggers_training():
    d = decide_retrain_v240(current_rows=1000, previous_rows=900, last_success_at="2026-01-01T00:00:00+00:00", shadow_outcomes_since_train=0, drift_severity=0.0, policy=policy())
    assert d.should_train
    assert "NEW_DATA_THRESHOLD" in d.reasons
    assert d.execution_authority == "NONE"


def test_unchanged_data_does_not_retrain_forever():
    d = decide_retrain_v240(current_rows=1000, previous_rows=1000, last_success_at="2026-08-25T00:00:00+00:00", shadow_outcomes_since_train=0, drift_severity=0.0, policy={**policy(), "maximum_model_age_hours": 999999})
    assert not d.should_train
    assert "NO_NEW_INFORMATION" in d.blockers


def test_shadow_or_drift_can_trigger_without_new_rows():
    d = decide_retrain_v240(current_rows=1000, previous_rows=1000, last_success_at="2026-01-01T00:00:00+00:00", shadow_outcomes_since_train=31, drift_severity=0.0, policy=policy())
    assert d.should_train
    assert "SHADOW_OUTCOME_THRESHOLD" in d.reasons


def test_failed_attempt_obeys_cooldown():
    d = decide_retrain_v240(current_rows=1000, previous_rows=0, last_success_at=None, last_attempt_at="2099-01-01T00:00:00+00:00", shadow_outcomes_since_train=0, drift_severity=0.0, policy={**policy(), "minimum_retrain_cooldown_hours": 6})
    assert not d.should_train
    assert "RETRAIN_COOLDOWN" in d.blockers
