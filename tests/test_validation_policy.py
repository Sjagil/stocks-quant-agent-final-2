from stocks.research.validation_policy import classify_generalization, promotion_from_evidence


POLICY = {
    "min_unseen_symbols_available": 5,
    "min_unseen_symbols_traded": 5,
    "min_oos_trades": 40,
    "min_positive_fold_ratio": 0.75,
    "min_stress_positive_fold_ratio": 0.75,
    "min_positive_symbol_ratio": 0.60,
    "min_stress_positive_symbol_ratio": 0.50,
    "max_symbol_trade_share": 0.35,
    "require_positive_median_expectancy": True,
    "require_positive_median_stress_expectancy": True,
}


def test_generalization_passes_robust_unseen_evidence():
    result = classify_generalization(
        unseen_symbols_available=12,
        unseen_symbols_traded=9,
        oos_trades=180,
        positive_fold_ratio=1.0,
        stress_positive_fold_ratio=0.75,
        median_expectancy_bps=22.0,
        median_stress_expectancy_bps=9.0,
        positive_symbol_ratio=0.67,
        stress_positive_symbol_ratio=0.56,
        max_symbol_trade_share=0.20,
        policy=POLICY,
    )
    assert result.status == "DYNAMIC_UNIVERSE_VALIDATED"
    assert result.passed is True
    assert result.evaluable is True


def test_generalization_insufficient_unseen_is_not_reject():
    result = classify_generalization(
        unseen_symbols_available=2,
        unseen_symbols_traded=2,
        oos_trades=100,
        positive_fold_ratio=1.0,
        stress_positive_fold_ratio=1.0,
        median_expectancy_bps=20.0,
        median_stress_expectancy_bps=10.0,
        positive_symbol_ratio=1.0,
        stress_positive_symbol_ratio=1.0,
        max_symbol_trade_share=0.50,
        policy=POLICY,
    )
    assert result.status == "NOT_EVALUABLE_INSUFFICIENT_UNSEEN_1H"
    assert result.evaluable is False


def test_generalization_rejects_concentrated_edge():
    result = classify_generalization(
        unseen_symbols_available=10,
        unseen_symbols_traded=7,
        oos_trades=100,
        positive_fold_ratio=1.0,
        stress_positive_fold_ratio=1.0,
        median_expectancy_bps=20.0,
        median_stress_expectancy_bps=10.0,
        positive_symbol_ratio=0.70,
        stress_positive_symbol_ratio=0.60,
        max_symbol_trade_share=0.55,
        policy=POLICY,
    )
    assert result.status == "DYNAMIC_UNIVERSE_REJECT"
    assert "max_symbol_trade_share" in result.reasons


def test_indicator_promotion_requires_both_layers():
    assert promotion_from_evidence(
        existing_stage="VALIDATION_QUEUE",
        crosscheck_status="CROSS_ENGINE_VALIDATED",
        generalization_status="PENDING",
    ) == "GENERALIZATION_QUEUE"
    assert promotion_from_evidence(
        existing_stage="VALIDATION_QUEUE",
        crosscheck_status="CROSS_ENGINE_VALIDATED",
        generalization_status="DYNAMIC_UNIVERSE_VALIDATED",
    ) == "FINALIST_CANDIDATE"


def test_existing_finalist_is_not_demoted():
    assert promotion_from_evidence(
        existing_stage="FINALIST_CANDIDATE",
        crosscheck_status="CROSS_ENGINE_REJECT",
        generalization_status="DYNAMIC_UNIVERSE_REJECT",
    ) == "FINALIST_CANDIDATE"
