import pandas as pd

from stocks.production.preflight_v2_41 import _broker_clock_drift_seconds


def test_broker_clock_drift_is_absolute_and_fail_closed_on_bad_timestamp():
    now = pd.Timestamp("2026-08-26T08:00:00Z")
    assert _broker_clock_drift_seconds("2026-08-26T08:00:07+00:00", now) == 7.0
    assert _broker_clock_drift_seconds("2026-08-26T07:59:53+00:00", now) == 7.0
    assert _broker_clock_drift_seconds("not-a-time", now) == float("inf")
