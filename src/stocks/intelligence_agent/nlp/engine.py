from __future__ import annotations

import math
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models import EventType, NewsArticle, NewsSignal


_EVENT_RULES: dict[EventType, tuple[str, ...]] = {
    EventType.EARNINGS: ("earnings", "eps", "revenue", "quarter", "profit", "loss"),
    EventType.GUIDANCE: ("guidance", "outlook", "forecast", "raises forecast", "cuts forecast"),
    EventType.M_AND_A: ("acquire", "acquisition", "merger", "takeover", "buyout"),
    EventType.ANALYST: ("upgrade", "downgrade", "price target", "analyst", "rating"),
    EventType.REGULATORY: ("regulator", "regulatory", "sec", "ftc", "doj", "approval", "ban"),
    EventType.LITIGATION: ("lawsuit", "litigation", "court", "settlement", "fine"),
    EventType.SUPPLY: ("supply", "production", "output", "inventory", "mine", "refinery", "opec"),
    EventType.DEMAND: ("demand", "orders", "shipments", "consumption", "sales"),
    EventType.MACRO: ("inflation", "cpi", "ppi", "gdp", "payroll", "fed", "ecb", "rates", "yield"),
    EventType.GEOPOLITICAL: ("war", "sanction", "tariff", "geopolitical", "conflict", "export control"),
    EventType.MANAGEMENT: ("ceo", "cfo", "resigns", "appointed", "management"),
    EventType.CAPITAL: ("buyback", "dividend", "offering", "issuance", "debt", "capital raise"),
}

_EVENT_SEVERITY = {
    EventType.EARNINGS: 0.75,
    EventType.GUIDANCE: 0.95,
    EventType.M_AND_A: 1.0,
    EventType.ANALYST: 0.45,
    EventType.REGULATORY: 0.9,
    EventType.LITIGATION: 0.75,
    EventType.SUPPLY: 0.85,
    EventType.DEMAND: 0.7,
    EventType.MACRO: 0.85,
    EventType.GEOPOLITICAL: 1.0,
    EventType.MANAGEMENT: 0.65,
    EventType.CAPITAL: 0.75,
    EventType.OTHER: 0.35,
}


class FinancialNLP:
    """Finance-specific NLP with deterministic fail-closed fallbacks.

    FinBERT is optional at import time so the rest of the engine can be tested
    without downloading a transformer model.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert", half_life_hours: float = 18.0) -> None:
        self.model_name = model_name
        self.half_life_hours = half_life_hours
        self._classifier = None
        self._vectorizer = HashingVectorizer(n_features=2**14, alternate_sign=False, norm="l2")
        self._recent_vectors: dict[str, deque] = defaultdict(lambda: deque(maxlen=128))

    def _load_classifier(self):
        if self._classifier is None:
            from transformers import pipeline

            self._classifier = pipeline("text-classification", model=self.model_name, truncation=True)
        return self._classifier

    def classify_article(
        self,
        article: NewsArticle,
        *,
        symbol_aliases: dict[str, Iterable[str]] | None = None,
        now: datetime | None = None,
        source_quality: float = 0.75,
    ) -> list[NewsSignal]:
        now = now or datetime.now(timezone.utc)
        text = f"{article.title}. {article.body}".strip()
        symbols = set(article.symbols)
        symbols.update(self._resolve_symbols(text, symbol_aliases or {}))
        if not symbols:
            return []

        sentiment, confidence = self._sentiment(text)
        event_type = self._event_type(text)
        severity = _EVENT_SEVERITY[event_type]
        age_hours = max(0.0, (now - article.published_at.astimezone(timezone.utc)).total_seconds() / 3600)
        time_decay = math.exp(-math.log(2) * age_hours / max(self.half_life_hours, 0.1))

        output: list[NewsSignal] = []
        for symbol in sorted(symbols):
            relevance = self._relevance(text, symbol, symbol_aliases or {})
            novelty = self._novelty(symbol, text)
            horizon = self._horizon(event_type)
            score = float(np.clip(
                sentiment
                * confidence
                * relevance
                * novelty
                * source_quality
                * severity
                * time_decay,
                -1.0,
                1.0,
            ))
            output.append(
                NewsSignal(
                    symbol=symbol,
                    published_at=article.published_at,
                    sentiment=sentiment,
                    confidence=confidence,
                    relevance=relevance,
                    novelty=novelty,
                    source_quality=source_quality,
                    event_type=event_type,
                    event_severity=severity,
                    horizon_days=horizon,
                    raw_score=score,
                    article_id=article.article_id,
                    rationale=f"{event_type.value}; sentiment={sentiment:+.2f}; novelty={novelty:.2f}; decay={time_decay:.2f}",
                )
            )
        return output

    def _sentiment(self, text: str) -> tuple[float, float]:
        try:
            result = self._load_classifier()(text[:6000])[0]
            label = str(result["label"]).lower()
            confidence = float(result["score"])
            if "positive" in label:
                return confidence, confidence
            if "negative" in label:
                return -confidence, confidence
            return 0.0, confidence
        except Exception:
            # Deterministic fallback. It is intentionally weak and low-confidence.
            positive = len(re.findall(r"\b(beat|beats|growth|upgrade|raises|record|strong|surge|profit)\b", text, re.I))
            negative = len(re.findall(r"\b(miss|cuts|downgrade|weak|fall|loss|lawsuit|ban|shortage)\b", text, re.I))
            net = positive - negative
            return float(np.tanh(net / 3.0)), 0.25

    def _event_type(self, text: str) -> EventType:
        lower = text.lower()
        best = (0, EventType.OTHER)
        for event_type, terms in _EVENT_RULES.items():
            hits = sum(term in lower for term in terms)
            if hits > best[0]:
                best = (hits, event_type)
        return best[1]

    def _resolve_symbols(self, text: str, aliases: dict[str, Iterable[str]]) -> set[str]:
        lower = text.lower()
        result: set[str] = set()
        for symbol, names in aliases.items():
            candidates = {symbol.lower(), *(str(x).lower() for x in names)}
            if any(re.search(rf"(?<!\w){re.escape(name)}(?!\w)", lower) for name in candidates if name):
                result.add(symbol.upper())
        return result

    def _relevance(self, text: str, symbol: str, aliases: dict[str, Iterable[str]]) -> float:
        names = [symbol, *aliases.get(symbol, ())]
        lower = text.lower()
        hits = sum(lower.count(str(name).lower()) for name in names if name)
        return float(np.clip(0.4 + 0.15 * hits, 0.4, 1.0))

    def _novelty(self, symbol: str, text: str) -> float:
        vector = self._vectorizer.transform([text])
        history = self._recent_vectors[symbol]
        if not history:
            novelty = 1.0
        else:
            sims = [float(cosine_similarity(vector, old)[0, 0]) for old in history]
            novelty = float(np.clip(1.0 - max(sims), 0.10, 1.0))
        history.append(vector)
        return novelty

    @staticmethod
    def _horizon(event_type: EventType) -> int:
        return {
            EventType.ANALYST: 3,
            EventType.EARNINGS: 5,
            EventType.GUIDANCE: 10,
            EventType.M_AND_A: 20,
            EventType.SUPPLY: 10,
            EventType.DEMAND: 10,
            EventType.MACRO: 5,
            EventType.GEOPOLITICAL: 5,
            EventType.REGULATORY: 20,
        }.get(event_type, 5)
