from __future__ import annotations

from .contracts import AgentDecisionEnvelope, AgentVote
from .marl import coordinate_roles


def fuse_agent_votes(
    *,
    symbol: str,
    fresh_validated_entry: bool,
    shariah_verified: bool,
    broker_account_ready: bool,
    validated_strategy: bool,
    current_exposure: float,
    timing_vote: AgentVote,
    sizing_vote: AgentVote,
    risk_vote: AgentVote,
    nlp_vote: AgentVote,
) -> AgentDecisionEnvelope:
    blockers: list[str] = []

    if not validated_strategy:
        blockers.append("VALIDATED_STRATEGY_REQUIRED")
    if not fresh_validated_entry and current_exposure <= 1e-12:
        blockers.append("FRESH_VALIDATED_ENTRY_REQUIRED")
    if not shariah_verified and current_exposure <= 1e-12:
        blockers.append("SHARIAH_VERIFIED_REQUIRED")
    if not broker_account_ready:
        blockers.append("IBKR_ACCOUNT_READY_REQUIRED")

    timing_action = (
        timing_vote.action
        if timing_vote.available
        else "HOLD"
    )
    sac_target = (
        float(sizing_vote.target_exposure)
        if (
            sizing_vote.available
            and sizing_vote.target_exposure is not None
        )
        else float(current_exposure)
    )
    sac_target = max(0.0, min(1.0, sac_target))

    modifier = (
        float(nlp_vote.modifier)
        if nlp_vote.available
        else 1.0
    )
    modifier = min(1.10, max(0.90, modifier))

    # NLP modifies sizing BEFORE the risk specialist. The risk specialist is
    # therefore the final learned exposure cap and cannot be undone by news.
    nlp_adjusted_target = max(
        0.0,
        min(1.0, sac_target * modifier),
    )

    risk_action = (
        risk_vote.action
        if risk_vote.available
        else "KEEP"
    )

    coordinated = coordinate_roles(
        current_exposure=current_exposure,
        timing_action=timing_action,
        sizing_target=nlp_adjusted_target,
        risk_action=risk_action,
    )

    hard_gates_pass = not blockers
    target = coordinated.resulting_exposure

    # Learned agents cannot manufacture a new entry around deterministic gates.
    if current_exposure <= 1e-12 and not hard_gates_pass:
        target = 0.0

    return AgentDecisionEnvelope(
        symbol=symbol.upper(),
        hard_gates_pass=hard_gates_pass,
        timing_action=timing_action,
        sac_target_exposure=sac_target,
        risk_capped_exposure=float(coordinated.resulting_exposure),
        nlp_modifier=modifier,
        shadow_target_exposure=float(target),
        votes=(
            timing_vote,
            sizing_vote,
            risk_vote,
            nlp_vote,
        ),
        blockers=tuple(sorted(set(blockers))),
    )
