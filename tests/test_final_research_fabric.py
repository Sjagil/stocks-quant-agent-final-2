
import pandas as pd

from stocks.research.final_strategy_roster import _components
from stocks.research.shariah_research_precheck import business_precheck
from stocks.research.validation_policy import promotion_from_evidence


def test_generalization_reject_is_terminal_stage():
    assert (
        promotion_from_evidence(
            existing_stage="VALIDATION_QUEUE",
            crosscheck_status="CROSS_ENGINE_VALIDATED",
            generalization_status="DYNAMIC_UNIVERSE_REJECT",
        )
        == "REJECTED_AFTER_GENERALIZATION"
    )


def test_generalization_validation_can_promote():
    assert (
        promotion_from_evidence(
            existing_stage="VALIDATION_QUEUE",
            crosscheck_status="CROSS_ENGINE_VALIDATED",
            generalization_status="DYNAMIC_UNIVERSE_VALIDATED",
        )
        == "FINALIST_CANDIDATE"
    )


def test_business_precheck_never_claims_compliance():
    result = business_precheck(
        sector="Technology",
        industry="Semiconductors",
        name="Example",
    )
    assert result["status"] == "NO_BUSINESS_EXCLUSION_FOUND"
    assert result["final_shariah_compliance"] is False
    assert result["execution_authority"] == "NONE"


def test_bank_is_hard_exclusion_candidate():
    result = business_precheck(
        sector="Financial Services",
        industry="Regional Banks",
        name="Example Bank",
    )
    assert result["status"] == "HARD_EXCLUSION_CANDIDATE"
    assert result["hard_matches"]


def test_redundancy_components_cluster_flagged_pair():
    pairs = pd.DataFrame(
        [
            {
                "left": "A",
                "right": "B",
                "redundancy_flag": True,
            },
            {
                "left": "B",
                "right": "C",
                "redundancy_flag": False,
            },
        ]
    )
    components = _components(["A", "B", "C"], pairs)
    assert {"A", "B"} in components
    assert {"C"} in components
