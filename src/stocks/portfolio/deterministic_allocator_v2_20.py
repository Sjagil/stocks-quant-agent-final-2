from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType

AUTHORITY_NONE = "NONE"
WEIGHT_TOLERANCE = 1e-12


class AssetKind(str, Enum):
    STOCK = "STOCK"
    ETF = "ETF"


def _finite(value: float, *, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _aware(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


@dataclass(frozen=True)
class AllocationPolicy:
    """Hard portfolio constraints for research and shadow decisions."""

    max_total_weight: float = 0.60
    max_stock_weight: float = 0.35
    max_etf_weight: float = 0.40
    max_open_positions: int = 3
    minimum_confidence: float = 0.50
    minimum_alpha_score: float = 0.0
    long_only: bool = True
    shariah_only: bool = True
    leverage_allowed: bool = False
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        total = _finite(self.max_total_weight, field="max_total_weight")
        stock = _finite(self.max_stock_weight, field="max_stock_weight")
        etf = _finite(self.max_etf_weight, field="max_etf_weight")
        confidence = _finite(self.minimum_confidence, field="minimum_confidence")
        minimum_alpha = _finite(
            self.minimum_alpha_score,
            field="minimum_alpha_score",
        )
        if not 0.0 < total <= 1.0:
            raise ValueError("max_total_weight must be in (0, 1]")
        if not 0.0 < stock <= total:
            raise ValueError("max_stock_weight must be in (0, max_total_weight]")
        if not 0.0 < etf <= total:
            raise ValueError("max_etf_weight must be in (0, max_total_weight]")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be positive")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("minimum_confidence must be in [0, 1]")
        if minimum_alpha < 0.0:
            raise ValueError("minimum_alpha_score cannot be negative")
        if not self.long_only:
            raise ValueError("v2.20 allocation must remain long-only")
        if not self.shariah_only:
            raise ValueError("v2.20 allocation must remain Shariah-only")
        if self.leverage_allowed:
            raise ValueError("v2.20 allocation cannot allow leverage")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("allocation policy cannot grant execution authority")

    def cap_for(self, asset_kind: AssetKind) -> float:
        if asset_kind is AssetKind.ETF:
            return self.max_etf_weight
        return self.max_stock_weight


@dataclass(frozen=True)
class AlphaProposal:
    symbol: str
    asset_kind: AssetKind
    alpha_score: float
    confidence: float
    data_cutoff: datetime
    strategy_ids: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    shariah_eligible: bool
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(
            self,
            "strategy_ids",
            tuple(sorted({str(item).strip() for item in self.strategy_ids if item})),
        )
        object.__setattr__(
            self,
            "hypothesis_ids",
            tuple(sorted({str(item).strip() for item in self.hypothesis_ids if item})),
        )
        if not self.strategy_ids or not self.hypothesis_ids:
            raise ValueError("proposal provenance cannot be empty")
        _finite(self.alpha_score, field="alpha_score")
        confidence = _finite(self.confidence, field="confidence")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        _aware(self.data_cutoff, field="data_cutoff")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("alpha proposal cannot grant execution authority")

    @property
    def strength(self) -> float:
        return max(0.0, float(self.alpha_score)) * float(self.confidence)


@dataclass(frozen=True)
class ProjectedTarget:
    symbol: str
    asset_kind: AssetKind
    target_weight: float
    alpha_score: float
    confidence: float
    data_cutoff: datetime
    strategy_ids: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        weight = _finite(self.target_weight, field="target_weight")
        if weight < 0.0:
            raise ValueError("target_weight cannot be negative")
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("projected target cannot grant execution authority")


@dataclass(frozen=True)
class ProjectionResult:
    targets: tuple[ProjectedTarget, ...]
    rejected: Mapping[str, tuple[str, ...]]
    total_weight: float
    cash_weight: float
    execution_authority: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejected", MappingProxyType(dict(self.rejected)))
        if self.execution_authority != AUTHORITY_NONE:
            raise ValueError("projection result cannot grant execution authority")


def _waterfill(
    proposals: list[AlphaProposal],
    policy: AllocationPolicy,
) -> dict[str, float]:
    remaining = float(policy.max_total_weight)
    active = list(proposals)
    weights = {proposal.symbol: 0.0 for proposal in proposals}

    while active and remaining > WEIGHT_TOLERANCE:
        total_strength = sum(proposal.strength for proposal in active)
        if total_strength <= WEIGHT_TOLERANCE:
            break
        capped: list[AlphaProposal] = []
        uncapped: list[AlphaProposal] = []
        for proposal in active:
            share = remaining * proposal.strength / total_strength
            capacity = policy.cap_for(proposal.asset_kind) - weights[proposal.symbol]
            if share >= capacity - WEIGHT_TOLERANCE:
                allocation = max(0.0, capacity)
                weights[proposal.symbol] += allocation
                remaining -= allocation
                capped.append(proposal)
            else:
                uncapped.append(proposal)
        if not capped:
            for proposal in uncapped:
                weights[proposal.symbol] += (
                    remaining * proposal.strength / total_strength
                )
            remaining = 0.0
            break
        active = uncapped

    return {
        symbol: round(max(0.0, value), 12)
        for symbol, value in weights.items()
        if value > WEIGHT_TOLERANCE
    }


def project_long_only(
    proposals: tuple[AlphaProposal, ...] | list[AlphaProposal],
    *,
    policy: AllocationPolicy | None = None,
) -> ProjectionResult:
    """Project ranked alpha proposals onto a feasible long-only portfolio.

    The result is deterministic for the same proposal set, including when the
    input order changes. Eligibility, position count, total exposure and
    instrument caps are hard constraints rather than reward penalties.
    """

    active_policy = policy or AllocationPolicy()
    proposal_list = list(proposals)
    symbols = [proposal.symbol for proposal in proposal_list]
    if len(symbols) != len(set(symbols)):
        raise ValueError("proposals must contain one aggregate row per symbol")

    rejected: dict[str, tuple[str, ...]] = {}
    eligible: list[AlphaProposal] = []
    for proposal in proposal_list:
        reasons: list[str] = []
        if not proposal.shariah_eligible:
            reasons.append("SHARIAH_NOT_VERIFIED")
        if proposal.alpha_score <= active_policy.minimum_alpha_score:
            reasons.append("ALPHA_NOT_POSITIVE")
        if proposal.confidence < active_policy.minimum_confidence:
            reasons.append("CONFIDENCE_BELOW_MINIMUM")
        if proposal.strength <= WEIGHT_TOLERANCE:
            reasons.append("ZERO_ALLOCATION_STRENGTH")
        if reasons:
            rejected[proposal.symbol] = tuple(dict.fromkeys(reasons))
        else:
            eligible.append(proposal)

    ranked = sorted(
        eligible,
        key=lambda proposal: (
            -proposal.strength,
            -proposal.confidence,
            proposal.symbol,
        ),
    )
    selected = ranked[: active_policy.max_open_positions]
    for proposal in ranked[active_policy.max_open_positions :]:
        rejected[proposal.symbol] = ("MAX_OPEN_POSITIONS",)

    weights = _waterfill(selected, active_policy)
    targets = tuple(
        ProjectedTarget(
            symbol=proposal.symbol,
            asset_kind=proposal.asset_kind,
            target_weight=weights[proposal.symbol],
            alpha_score=proposal.alpha_score,
            confidence=proposal.confidence,
            data_cutoff=proposal.data_cutoff,
            strategy_ids=proposal.strategy_ids,
            hypothesis_ids=proposal.hypothesis_ids,
        )
        for proposal in selected
        if proposal.symbol in weights
    )
    total_weight = round(sum(target.target_weight for target in targets), 12)
    if total_weight > active_policy.max_total_weight + WEIGHT_TOLERANCE:
        raise AssertionError("projection exceeded max_total_weight")
    for target in targets:
        if (
            target.target_weight
            > active_policy.cap_for(target.asset_kind) + WEIGHT_TOLERANCE
        ):
            raise AssertionError(f"projection exceeded instrument cap: {target.symbol}")

    return ProjectionResult(
        targets=targets,
        rejected=dict(sorted(rejected.items())),
        total_weight=total_weight,
        cash_weight=round(1.0 - total_weight, 12),
    )


__all__ = [
    "AUTHORITY_NONE",
    "AllocationPolicy",
    "AlphaProposal",
    "AssetKind",
    "ProjectedTarget",
    "ProjectionResult",
    "project_long_only",
]
