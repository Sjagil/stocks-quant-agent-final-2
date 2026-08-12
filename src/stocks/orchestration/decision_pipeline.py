from __future__ import annotations

from datetime import datetime, timezone

from stocks.contracts import IntentAction, TradeIntent
from stocks.intelligence_agent.models import PortfolioPlan
from stocks.rl.shadow_policy import RLSuggestion


def portfolio_plan_to_intents(
    plan: PortfolioPlan,
    *,
    rl_shadow: dict[str, RLSuggestion] | None = None,
) -> tuple[TradeIntent, ...]:
    """Translate portfolio targets into execution-neutral intents.

    RL information is attached as metadata only. It does not resize or authorize
    an intent until a separately validated promotion policy is implemented.
    """
    rl_shadow = rl_shadow or {}
    intents: list[TradeIntent] = []
    now = datetime.now(timezone.utc)
    for target in plan.targets:
        action = IntentAction(target.action) if target.action in IntentAction._value2member_map_ else IntentAction.HOLD
        shadow = rl_shadow.get(target.symbol)
        metadata = {
            "portfolio_plan_created_at": plan.created_at.isoformat(),
            "plan_execution_authority": plan.execution_authority,
        }
        if shadow is not None:
            metadata["rl_shadow"] = {
                "target_position": shadow.target_position,
                "confidence": shadow.confidence,
                "model_id": shadow.model_id,
                "execution_authority": shadow.execution_authority,
            }
        intents.append(
            TradeIntent(
                created_at=now,
                symbol=target.symbol,
                action=action,
                target_weight=target.target_weight,
                target_notional_eur=target.target_notional,
                confidence=target.confidence,
                source="market_intelligence_allocator",
                execution_authority="NONE",
                rationale=target.rationale,
                metadata=metadata,
            )
        )
    return tuple(intents)
