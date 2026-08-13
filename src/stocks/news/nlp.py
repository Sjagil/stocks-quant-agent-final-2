from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class SentimentResult:
    score: float
    confidence: float
    label: str
    backend: str


def _signed_label(
    label: str,
    confidence: float,
) -> float:
    normalized = (
        label.lower()
    )

    if (
        "positive"
        in normalized
    ):
        return float(
            confidence
        )

    if (
        "negative"
        in normalized
    ):
        return -float(
            confidence
        )

    return 0.0


@lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline

    model = os.environ.get(
        "WM_FINANCIAL_NLP_MODEL",
        "ProsusAI/finbert",
    )

    return pipeline(
        "text-classification",
        model=model,
        tokenizer=model,
        truncation=True,
    )


def financial_sentiment(
    text: str,
) -> SentimentResult:
    clean = (
        str(
            text
        )
        .strip()
    )

    if not clean:
        return SentimentResult(
            score=0.0,
            confidence=0.0,
            label="empty",
            backend="none",
        )

    try:
        output = _pipeline()(
            clean[:5000]
        )

        row = output[0]

        label = str(
            row.get(
                "label",
                "neutral",
            )
        )

        confidence = float(
            row.get(
                "score",
                0.0,
            )
        )

        return SentimentResult(
            score=_signed_label(
                label,
                confidence,
            ),
            confidence=confidence,
            label=label,
            backend="transformers",
        )

    except Exception:
        return SentimentResult(
            score=0.0,
            confidence=0.0,
            label="unavailable",
            backend="fallback",
        )
