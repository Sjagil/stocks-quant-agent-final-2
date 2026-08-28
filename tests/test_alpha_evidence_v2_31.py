from stocks.research.alpha_evidence_v2_31 import AlphaEvidence, combine_alpha_evidence


def test_rejected_feature_has_zero_weight_and_promoted_features_combine():
    promoted=AlphaEvidence("f","TREND",1.0,1.2,"PROMOTE_RESEARCH",0.08,0.8,0.7,regime_multiplier=0.9)
    rejected=AlphaEvidence("g","MOMENTUM",1.0,3.0,"REJECT_OR_REVIEW",0.2,2.0,0.9)
    assert promoted.predictive_weight > 0
    assert rejected.predictive_weight == 0
    result=combine_alpha_evidence([promoted,rejected])
    assert result["active_features"] == 1
    assert result["alpha_evidence_score"] == 1.2
    assert 0 < result["confidence"] < 1
