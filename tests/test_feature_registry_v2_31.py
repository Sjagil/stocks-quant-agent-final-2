from stocks.research.feature_registry_v2_31 import FeatureFamily, FeatureSpec, default_feature_registry


def test_default_registry_is_causal_unique_and_broad():
    registry = default_feature_registry()
    assert len(registry.ids()) >= 15
    assert len(registry.ids()) == len(set(registry.ids()))
    assert registry.get("trend_regression_slope_20").family is FeatureFamily.TREND
    assert registry.get("news_weighted_sentiment").point_in_time is True
    assert registry.as_dict()["execution_authority"] == "NONE"


def test_registry_rejects_non_causal_feature():
    try:
        FeatureSpec("future_leak", FeatureFamily.PRICE, "bad", causal=False)
    except ValueError as exc:
        assert "causal" in str(exc)
    else:
        raise AssertionError("non-causal feature should fail")
