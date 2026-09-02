from __future__ import annotations

import hashlib
import itertools
import json
import random
from dataclasses import replace
from typing import Any, Mapping

from .strategy_dna_v2_32 import StrategyDNA
from .strategy_family_registry_v2_32 import StrategyFamilyTemplate, family_registry


def _seed(family: str, seed: int) -> int:
    raw = hashlib.sha256(f"v2.32|{seed}|{family}".encode()).hexdigest()
    return int(raw[:12], 16) % 2_147_483_647


def _params_valid(params: Mapping[str, Any]) -> bool:
    pairs = (("beta_min", "beta_max"), ("vol_min", "vol_max"))
    for low, high in pairs:
        if low in params and high in params and float(params[low]) >= float(params[high]):
            return False
    return True


def sample_parameter_variants(template: StrategyFamilyTemplate, *, maximum: int, seed: int) -> list[dict[str, Any]]:
    if maximum <= 0:
        raise ValueError("maximum must be positive")
    base = dict(template.default_parameters)
    result = [base]
    seen = {json.dumps(base, sort_keys=True, default=str)}
    for key, values in template.parameter_space.items():
        for value in values:
            candidate = dict(base)
            candidate[key] = value
            marker = json.dumps(candidate, sort_keys=True, default=str)
            if marker not in seen and _params_valid(candidate):
                result.append(candidate); seen.add(marker)
            if len(result) >= maximum:
                return result
    keys = tuple(template.parameter_space)
    combos = list(itertools.product(*(template.parameter_space[key] for key in keys)))
    rng = random.Random(_seed(template.family, seed)); rng.shuffle(combos)
    for values in combos:
        candidate = dict(zip(keys, values, strict=True))
        marker = json.dumps(candidate, sort_keys=True, default=str)
        if marker in seen or not _params_valid(candidate):
            continue
        result.append(candidate); seen.add(marker)
        if len(result) >= maximum:
            break
    return result


def instantiate_template(template: StrategyFamilyTemplate, params: Mapping[str, Any], *, variant_index: int) -> StrategyDNA:
    return StrategyDNA(
        family=template.family,
        variant_name=f"{template.family}__v{variant_index:03d}",
        universe_id=template.universe_id,
        primary_timeframe=template.primary_timeframe,
        regime_allowlist=template.regime_allowlist,
        setup_features=template.setup_features,
        entry_conditions=template.entry_conditions,
        filter_conditions=template.filter_conditions,
        exit_conditions=template.exit_conditions,
        stop=template.stop,
        sizing=template.sizing,
        horizon=template.horizon,
        parameters=dict(params),
        rationale=template.rationale,
    )


def generate_strategy_dna(
    *,
    maximum_variants_per_family: int = 8,
    seed: int = 32,
    enabled_families: set[str] | None = None,
) -> list[StrategyDNA]:
    candidates: list[StrategyDNA] = []
    for template in family_registry():
        if enabled_families is not None and template.family not in enabled_families:
            continue
        variants = sample_parameter_variants(template, maximum=maximum_variants_per_family, seed=seed)
        for index, params in enumerate(variants):
            dna = instantiate_template(template, params, variant_index=index)
            if dna.complexity <= template.max_complexity:
                candidates.append(dna)
    ids = [candidate.dna_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise AssertionError("strategy DNA collision")
    return candidates


__all__ = ["generate_strategy_dna", "instantiate_template", "sample_parameter_variants"]
