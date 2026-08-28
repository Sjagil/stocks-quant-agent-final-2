from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .strategy_dna_v2_32 import StrategyDNA


@dataclass(frozen=True)
class StrategyProvenance:
    dna_id: str
    dna_sha256: str
    governance_sha256: str
    generator_config_sha256: str
    source_branch: str
    source_commit: str
    source_engine: str = "strategy_generator_v2_32"
    parameters_frozen_for_handoff: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def build_strategy_provenance(
    dna: StrategyDNA,
    *,
    governance: Mapping[str, object],
    generator_config: Mapping[str, object],
    source_branch: str,
    source_commit: str,
) -> StrategyProvenance:
    subset = {key: governance.get(key) for key in sorted(dna.all_feature_ids)}
    return StrategyProvenance(
        dna_id=dna.dna_id,
        dna_sha256=_digest(dna.as_dict()),
        governance_sha256=_digest(subset),
        generator_config_sha256=_digest(dict(generator_config)),
        source_branch=source_branch,
        source_commit=source_commit,
    )


__all__ = ["StrategyProvenance", "build_strategy_provenance"]
