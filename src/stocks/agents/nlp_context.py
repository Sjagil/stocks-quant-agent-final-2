from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NLPContext:
    symbol: str
    sentiment: float
    confidence: float
    modifier: float
    stories: int
    source: str
    execution_authority: str = "NONE"


def bounded_modifier(
    sentiment: float,
    confidence: float,
    *,
    minimum: float = 0.90,
    maximum: float = 1.10,
) -> float:
    raw = 1.0 + 0.10 * float(sentiment) * float(confidence)
    return float(min(max(raw, minimum), maximum))


def _latest_news_artifact(root: Path) -> Path | None:
    directory = root / "artifacts/evidence/news"
    if not directory.is_dir():
        return None
    files = sorted(directory.glob("*-news.json"))
    return files[-1] if files else None


def read_nlp_context(
    project_root: str | Path,
    symbol: str,
) -> NLPContext:
    root = Path(project_root).resolve()
    path = _latest_news_artifact(root)
    if path is None:
        return NLPContext(
            symbol=symbol.upper(),
            sentiment=0.0,
            confidence=0.0,
            modifier=1.0,
            stories=0,
            source="NO_NEWS_ARTIFACT",
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = list((payload.get("symbols") or {}).get(symbol.upper()) or [])

    weighted = 0.0
    weight_total = 0.0
    usable = 0

    for row in rows[:20]:
        try:
            sentiment = float(row.get("sentiment", 0.0))
            evidence_score = float(row.get("evidence_score", 0.0))
        except (TypeError, ValueError):
            continue

        if not (
            math.isfinite(sentiment)
            and math.isfinite(evidence_score)
        ):
            continue

        weight = max(0.0, min(1.0, evidence_score))
        weighted += sentiment * weight
        weight_total += weight
        usable += 1

    score = weighted / weight_total if weight_total > 0 else 0.0
    confidence = min(1.0, weight_total / max(float(usable), 1.0))

    return NLPContext(
        symbol=symbol.upper(),
        sentiment=float(max(-1.0, min(1.0, score))),
        confidence=float(max(0.0, min(1.0, confidence))),
        modifier=bounded_modifier(score, confidence),
        stories=usable,
        source=str(path),
    )
