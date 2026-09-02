#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from stocks.news.nlp import financial_sentiment
if __name__ == "__main__":
    result = financial_sentiment("Corporate earnings improved and guidance was raised.")
    payload = {"backend": result.backend, "label": result.label, "confidence": result.confidence, "score": result.score}
    print(json.dumps(payload, indent=2))
    if result.backend != "transformers":
        raise SystemExit("FINBERT_NOT_READY")
    print("FINBERT_V2_42_READY")
