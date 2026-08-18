from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .contracts_v2_21 import (
    DEPLOYMENT_MODE,
    EXECUTION_AUTHORITY,
    PromotionPolicyV221,
)
from .splits import WalkForwardSplit, purged_walk_forward_splits


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


@dataclass(frozen=True)
class SeedEvaluationV221:
    seed: int
    fold_net_returns: tuple[float, ...]
    strategy_return: float
    baseline_return: float
    cost_stress_return: float
    severe_stress_return: float
    maximum_drawdown: float
    maximum_concentration: float
    reproducible: bool
    constraint_violations: int = 0

    def __post_init__(self) -> None:
        if not self.fold_net_returns:
            raise ValueError("each seed evaluation requires out-of-sample folds")
        numeric = (
            *self.fold_net_returns,
            self.strategy_return,
            self.baseline_return,
            self.cost_stress_return,
            self.severe_stress_return,
            self.maximum_drawdown,
            self.maximum_concentration,
        )
        if not np.isfinite(numeric).all():
            raise ValueError("seed metrics must be finite")
        if not 0 <= self.maximum_drawdown < 1:
            raise ValueError("maximum_drawdown must be in [0, 1)")
        if not 0 <= self.maximum_concentration <= 1:
            raise ValueError("maximum_concentration must be in [0, 1]")
        if self.constraint_violations < 0:
            raise ValueError("constraint_violations cannot be negative")


@dataclass(frozen=True)
class RLPromotionEvidenceV221:
    algorithm: str
    seeds: tuple[SeedEvaluationV221, ...]
    deflated_sharpe_probability: float
    expectancy_ci_lower_bps: float
    regime_coverage_complete: bool
    environment_contract_hash: str
    code_commit: str

    def __post_init__(self) -> None:
        if not self.algorithm:
            raise ValueError("algorithm is required")
        if not 0 <= self.deflated_sharpe_probability <= 1:
            raise ValueError("deflated_sharpe_probability must be in [0, 1]")
        if not np.isfinite(self.expectancy_ci_lower_bps):
            raise ValueError("expectancy_ci_lower_bps must be finite")
        if not _valid_sha256(self.environment_contract_hash.lower()):
            raise ValueError("environment_contract_hash must be SHA-256")
        if len(self.code_commit.strip()) < 7:
            raise ValueError("code_commit must contain an identifiable revision")


@dataclass(frozen=True)
class RLPromotionDecisionV221:
    algorithm: str
    research_ready: bool
    status: str
    blockers: tuple[str, ...]
    seed_count: int
    seed_wins: int
    positive_fold_ratio: float
    deflated_sharpe_probability: float
    expectancy_ci_lower_bps: float
    deployment_mode: str = DEPLOYMENT_MODE
    automatic_live_promotion: bool = False
    execution_authority: str = EXECUTION_AUTHORITY
    broker_calls: int = 0
    order_calls: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_rl_promotion_v221(
    evidence: RLPromotionEvidenceV221,
    *,
    policy: PromotionPolicyV221 | None = None,
) -> RLPromotionDecisionV221:
    """Fail-closed research gate. Passing never grants execution authority."""

    gates = policy or PromotionPolicyV221()
    blockers: list[str] = []
    if evidence.algorithm not in {"MAPPO", "MATD3"}:
        blockers.append("UNSUPPORTED_ALGORITHM")
    seeds_by_id = {row.seed: row for row in evidence.seeds}
    expected = set(gates.required_seeds)
    observed = set(seeds_by_id)
    if observed != expected or len(evidence.seeds) != len(expected):
        blockers.append("EXACT_TEN_SEEDS_REQUIRED")

    folds = [value for row in evidence.seeds for value in row.fold_net_returns]
    fold_counts = {len(row.fold_net_returns) for row in evidence.seeds}
    if len(fold_counts) != 1:
        blockers.append("INCONSISTENT_FOLD_COUNT")
    positive_fold_ratio = float(np.mean(np.asarray(folds) > 0)) if folds else 0.0
    if positive_fold_ratio < gates.minimum_positive_fold_ratio:
        blockers.append("POSITIVE_OOS_FOLD_RATIO_FAILED")

    seed_wins = sum(row.strategy_return > row.baseline_return for row in evidence.seeds)
    if seed_wins < gates.minimum_seed_wins:
        blockers.append("BASELINE_SEED_WIN_GATE_FAILED")
    if evidence.deflated_sharpe_probability < gates.minimum_deflated_sharpe_probability:
        blockers.append("DEFLATED_SHARPE_GATE_FAILED")
    if evidence.expectancy_ci_lower_bps <= gates.minimum_expectancy_ci_lower_bps:
        blockers.append("EXPECTANCY_CONFIDENCE_INTERVAL_FAILED")
    if not evidence.regime_coverage_complete:
        blockers.append("REGIME_COVERAGE_INCOMPLETE")
    if any(
        row.cost_stress_return <= gates.minimum_cost_stress_return
        for row in evidence.seeds
    ):
        blockers.append("COST_STRESS_1_5X_FAILED")
    if any(
        row.severe_stress_return < gates.minimum_severe_stress_return
        for row in evidence.seeds
    ):
        blockers.append("COST_STRESS_2_0X_FAILED")
    if any(row.maximum_drawdown > gates.maximum_drawdown for row in evidence.seeds):
        blockers.append("MAXIMUM_DRAWDOWN_FAILED")
    if any(
        row.maximum_concentration > gates.maximum_concentration
        for row in evidence.seeds
    ):
        blockers.append("CONCENTRATION_GATE_FAILED")
    if any(not row.reproducible for row in evidence.seeds):
        blockers.append("REPRODUCIBILITY_FAILED")
    if any(row.constraint_violations != 0 for row in evidence.seeds):
        blockers.append("HARD_CONSTRAINT_VIOLATION")

    unique_blockers = tuple(dict.fromkeys(blockers))
    ready = not unique_blockers
    return RLPromotionDecisionV221(
        algorithm=evidence.algorithm,
        research_ready=ready,
        status="SHADOW_RESEARCH_READY" if ready else "RESEARCH_REJECTED",
        blockers=unique_blockers,
        seed_count=len(evidence.seeds),
        seed_wins=seed_wins,
        positive_fold_ratio=positive_fold_ratio,
        deflated_sharpe_probability=evidence.deflated_sharpe_probability,
        expectancy_ci_lower_bps=evidence.expectancy_ci_lower_bps,
    )


def build_walk_forward_plan_v221(
    sample_count: int,
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    purge: int,
    embargo: int,
) -> tuple[WalkForwardSplit, ...]:
    splits = tuple(
        purged_walk_forward_splits(
            sample_count,
            train_size=train_size,
            validation_size=validation_size,
            test_size=test_size,
            purge=purge,
            embargo=embargo,
            step_size=test_size,
        )
    )
    if not splits:
        raise ValueError("walk-forward configuration produces no complete fold")
    for split in splits:
        if split.train_end + purge != split.validation_start:
            raise RuntimeError("training purge was not preserved")
        if split.validation_end + embargo != split.test_start:
            raise RuntimeError("test embargo was not preserved")
    return splits


@dataclass(frozen=True)
class SeedLedgerEntryV221:
    sequence: int
    previous_hash: str
    record: dict[str, Any]
    entry_hash: str


class ImmutableSeedLedgerV221:
    """Append-only, hash-chained ledger for seeds, folds and artifacts."""

    genesis_hash = "0" * 64

    def __init__(self) -> None:
        self._entries: list[SeedLedgerEntryV221] = []

    @staticmethod
    def _canonical(record: dict[str, Any]) -> str:
        return json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @classmethod
    def _hash(cls, sequence: int, previous_hash: str, record: dict[str, Any]) -> str:
        payload = f"{sequence}:{previous_hash}:{cls._canonical(record)}".encode()
        return hashlib.sha256(payload).hexdigest()

    def append(self, record: dict[str, Any]) -> SeedLedgerEntryV221:
        required = {"algorithm", "seed", "fold", "config_hash", "artifact_hash"}
        missing = sorted(required - set(record))
        if missing:
            raise ValueError(f"ledger record missing fields: {missing}")
        if not _valid_sha256(str(record["config_hash"]).lower()):
            raise ValueError("config_hash must be SHA-256")
        if not _valid_sha256(str(record["artifact_hash"]).lower()):
            raise ValueError("artifact_hash must be SHA-256")
        sequence = len(self._entries)
        previous = self._entries[-1].entry_hash if self._entries else self.genesis_hash
        copied = json.loads(self._canonical(record))
        entry = SeedLedgerEntryV221(
            sequence=sequence,
            previous_hash=previous,
            record=copied,
            entry_hash=self._hash(sequence, previous, copied),
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> tuple[SeedLedgerEntryV221, ...]:
        return tuple(self._entries)

    def validate(self) -> bool:
        previous = self.genesis_hash
        for sequence, entry in enumerate(self._entries):
            if entry.sequence != sequence or entry.previous_hash != previous:
                return False
            if entry.entry_hash != self._hash(sequence, previous, entry.record):
                return False
            previous = entry.entry_hash
        return True

    def to_jsonl(self) -> str:
        return "\n".join(self._canonical(asdict(entry)) for entry in self._entries) + (
            "\n" if self._entries else ""
        )

    @classmethod
    def from_entries(
        cls,
        entries: Iterable[SeedLedgerEntryV221],
    ) -> ImmutableSeedLedgerV221:
        ledger = cls()
        ledger._entries = list(entries)
        if not ledger.validate():
            raise ValueError("seed ledger hash chain is invalid")
        return ledger
