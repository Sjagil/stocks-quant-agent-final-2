
import pandas as pd

from stocks.research.final_strategy_roster import (
    _components,
    build_final_strategy_roster,
)
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


def test_redundancy_champion_uses_evidence_not_hypothesis_sort(tmp_path):
    registry_root = (
        tmp_path / "artifacts/research_runtime/research_candidate_registry"
    )
    redundancy_root = (
        tmp_path / "artifacts/research_runtime/strategy_redundancy"
    )
    registry_root.mkdir(parents=True)
    redundancy_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "hypothesis_id": "aaa-low-score",
                "strategy": "low",
                "family": "generated",
                "promotion_stage": "FINALIST_CANDIDATE",
                "generalization_status": "DYNAMIC_UNIVERSE_VALIDATED",
                "robustness_score": 10.0,
                "median_stress_test_expectancy_bps": 2.0,
                "median_test_expectancy_bps": 5.0,
                "queue_rank": 2,
            },
            {
                "hypothesis_id": "zzz-high-score",
                "strategy": "high",
                "family": "generated",
                "promotion_stage": "FINALIST_CANDIDATE",
                "generalization_status": "DYNAMIC_UNIVERSE_VALIDATED",
                "robustness_score": 80.0,
                "median_stress_test_expectancy_bps": 20.0,
                "median_test_expectancy_bps": 30.0,
                "queue_rank": 1,
            },
        ]
    ).to_csv(registry_root / "registry.csv", index=False)
    pd.DataFrame(
        [
            {
                "left": "aaa-low-score",
                "right": "zzz-high-score",
                "redundancy_flag": True,
            }
        ]
    ).to_csv(redundancy_root / "pairs.csv", index=False)

    roster, audit = build_final_strategy_roster(tmp_path)
    champion = roster.loc[roster["cluster_champion"].astype(bool)].iloc[0]
    alternate = roster.loc[~roster["cluster_champion"].astype(bool)].iloc[0]
    assert champion["hypothesis_id"] == "zzz-high-score"
    assert champion["roster_status"] == "BROADLY_VALIDATED_FINALIST"
    assert alternate["roster_status"] == "REDUNDANT_ALTERNATE"
    assert audit["broadly_validated_finalists"] == 1
