#!/usr/bin/env python3
from pathlib import Path

from stocks.research.research_candidate_registry import write_research_candidate_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    frame, audit, path = write_research_candidate_registry(ROOT)
    print("RESEARCH_CANDIDATE_REGISTRY", "CANDIDATES", audit["candidate_count"], "FINALISTS", audit["finalist_count"], "CHALLENGERS", audit["challenger_count"], "GENERALIZATION_QUEUE", audit["generalization_queue_count"], "VALIDATION_QUEUE", audit["validation_queue_count"], "CROSS_ENGINE_VALIDATED", audit["cross_engine_validated_count"], "DYNAMIC_GENERALIZED", audit["dynamic_universe_generalized_count"])
    if not frame.empty:
        columns = [c for c in ["hypothesis_id", "strategy", "family", "source_engine", "research_status", "validation_status", "cross_engine_status", "generalization_status", "promotion_stage"] if c in frame.columns]
        print(frame[columns].to_string(index=False))
    print("OUTPUT", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
