from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .feature_registry_v2_31 import FeatureRegistry, default_feature_registry
from .strategy_candidate_scoring_v2_32 import score_strategy_candidate
from .strategy_diversity_v2_32 import select_diverse_candidates
from .strategy_feasibility_v2_32 import evaluate_strategy_feasibility
from .strategy_generation_v2_32 import generate_strategy_dna
from .strategy_handoff_v2_32 import build_research_handoff
from .strategy_provenance_v2_32 import build_strategy_provenance


@dataclass(frozen=True)
class StrategyGeneratorV232Result:
    generated_count: int
    feasible_count: int
    selected_count: int
    family_count: int
    rejected_count: int
    candidates: tuple[dict[str, object], ...]
    handoffs: tuple[dict[str, object], ...]
    research_compliance_gate_applied: bool = False
    broker_submission_enabled: bool = False
    automatic_live_promotion: bool = False
    order_calls: int = 0
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_strategy_generator(
    governance: Mapping[str, Mapping[str, object]],
    *,
    registry: FeatureRegistry | None = None,
    maximum_variants_per_family: int = 8,
    maximum_selected: int = 48,
    max_similarity: float = 0.88,
    max_per_family: int = 3,
    seed: int = 32,
    generator_config: Mapping[str, object] | None = None,
    source_branch: str = "UNKNOWN",
    source_commit: str = "UNKNOWN",
) -> StrategyGeneratorV232Result:
    reg = registry or default_feature_registry()
    generated = generate_strategy_dna(maximum_variants_per_family=maximum_variants_per_family, seed=seed)
    feasible = []
    score_by_id = {}
    candidate_rows = []
    for dna in generated:
        feasibility = evaluate_strategy_feasibility(dna, governance=governance, registry=reg)
        score = score_strategy_candidate(dna, governance)
        score_by_id[dna.dna_id] = score
        candidate_rows.append({
            "dna_id": dna.dna_id,
            "family": dna.family,
            "variant_name": dna.variant_name,
            "feasibility": feasibility.status,
            "blockers": list(feasibility.blockers),
            "priority_score": score.score,
            "complexity": dna.complexity,
            "features": list(dna.all_feature_ids),
            "parameters": dict(dna.parameters),
            "execution_authority": "NONE",
        })
        if feasibility.status == "ELIGIBLE_RESEARCH":
            feasible.append(dna)
    ranked = sorted(feasible, key=lambda dna: (-score_by_id[dna.dna_id].score, dna.family, dna.dna_id))
    selected = select_diverse_candidates(ranked, maximum=maximum_selected, max_similarity=max_similarity, max_per_family=max_per_family)
    cfg = dict(generator_config or {})
    handoffs = []
    for dna in selected:
        provenance = build_strategy_provenance(
            dna,
            governance=governance,
            generator_config=cfg,
            source_branch=source_branch,
            source_commit=source_commit,
        )
        handoffs.append(build_research_handoff(dna, provenance, priority_score=score_by_id[dna.dna_id].score).as_dict())
    return StrategyGeneratorV232Result(
        generated_count=len(generated),
        feasible_count=len(feasible),
        selected_count=len(selected),
        family_count=len({dna.family for dna in selected}),
        rejected_count=len(generated) - len(feasible),
        candidates=tuple(candidate_rows),
        handoffs=tuple(handoffs),
    )


__all__ = ["StrategyGeneratorV232Result", "run_strategy_generator"]
