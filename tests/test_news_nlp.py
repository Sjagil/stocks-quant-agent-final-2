from stocks.news.nlp import _signed_label


def test_signed_positive_sentiment() -> None:
    assert (
        _signed_label(
            "positive",
            0.9,
        )
        == 0.9
    )


def test_signed_negative_sentiment() -> None:
    assert (
        _signed_label(
            "negative",
            0.8,
        )
        == -0.8
    )


def test_neutral_sentiment_is_zero() -> None:
    assert (
        _signed_label(
            "neutral",
            0.99,
        )
        == 0.0
    )
