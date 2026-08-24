from __future__ import annotations
import hashlib
import json
from .contracts_v2_37 import ShadowDecisionV237

def canonical_idempotency_key(decision: ShadowDecisionV237) -> str:
    payload = {
        "strategy_id": decision.strategy_id,
        "symbol": decision.symbol,
        "decision_time": decision.decision_time,
        "side": decision.side.value,
        "intent": decision.intent,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def deterministic_identifier(prefix: str, key: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{key}".encode()).hexdigest()[:24]
    return f"{prefix}_{digest}"

__all__ = ["canonical_idempotency_key", "deterministic_identifier"]
