from __future__ import annotations

import pandas as pd


def test_validation_queue_contract_is_non_authoritative() -> None:
    row = {
        "promotion_stage": "VALIDATION_QUEUE",
        "cross_engine_validated": False,
        "dynamic_universe_generalized": False,
        "execution_authority": "NONE",
    }
    assert row["promotion_stage"] != "FINALIST_CANDIDATE"
    assert row["cross_engine_validated"] is False
    assert row["execution_authority"] == "NONE"


def test_candidate_registry_stage_order_is_explicit() -> None:
    stages = pd.Series(["FINALIST_CANDIDATE", "CHALLENGER", "VALIDATION_QUEUE"])
    assert set(stages) == {"FINALIST_CANDIDATE", "CHALLENGER", "VALIDATION_QUEUE"}
