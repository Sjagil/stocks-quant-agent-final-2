from __future__ import annotations

from collections import defaultdict

from .strategy_dna_v2_32 import StrategyDNA


def feature_jaccard(a: StrategyDNA, b: StrategyDNA) -> float:
    left, right = set(a.all_feature_ids), set(b.all_feature_ids)
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def strategy_similarity(a: StrategyDNA, b: StrategyDNA) -> float:
    feature = feature_jaccard(a, b)
    family = 1.0 if a.family == b.family else 0.0
    regime = len(set(a.regime_allowlist) & set(b.regime_allowlist)) / max(1, len(set(a.regime_allowlist) | set(b.regime_allowlist)))
    return 0.65 * feature + 0.25 * family + 0.10 * regime


def select_diverse_candidates(
    ranked: list[StrategyDNA],
    *,
    maximum: int,
    max_similarity: float = 0.88,
    max_per_family: int = 3,
) -> list[StrategyDNA]:
    if maximum <= 0:
        return []
    selected: list[StrategyDNA] = []
    family_counts: dict[str, int] = defaultdict(int)
    for candidate in ranked:
        if family_counts[candidate.family] >= max_per_family:
            continue
        if any(strategy_similarity(candidate, existing) > max_similarity for existing in selected):
            continue
        selected.append(candidate)
        family_counts[candidate.family] += 1
        if len(selected) >= maximum:
            break
    return selected


__all__ = ["feature_jaccard", "select_diverse_candidates", "strategy_similarity"]
