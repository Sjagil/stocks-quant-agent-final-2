# v2.39.1 Continuous Research Hardening

This release hardens the v2.39 persistent research runtime without replacing its SQLite database, job queue, experiment registry, or historical evidence.

## Core changes

- `REGISTRY_SNAPSHOT` is upstream metadata and never counts as independent outcome evidence.
- Champion review requires `VALIDATED` upstream status, cross-engine validation, dynamic-universe generalization, at least two independent evidence classes, at least two independent source groups, positive OOS **or** sufficient positive shadow evidence, positive >=2x cost stress, fresh outcome evidence, and a minimum quality score.
- Quality score is evidence-weighted instead of defaulting every healthy strategy to `1.0`.
- Positive audit reasons and missing requirements are exported for every entity.
- `approve-role --role CHAMPION` fails closed unless the hardened champion gate passes.
- Known upstream artifacts are ingested as direct evidence for diagnostics, but a registry-derived cost-stress summary is deliberately tagged 1x and cannot satisfy the hard 2x gate.

## Runtime outputs

The existing runtime DB remains at `artifacts/research_runtime/continuous_quant_research_v2_39/research.db`. v2.39.1 adds:

- `quality_scorecard_v2_39_1.csv`
- `champion_review_queue_v2_39_1.csv`
- `evidence_gaps_v2_39_1.csv`
- `retirement_watch_v2_39_1.csv`
- `status_v2_39_1.json`
- `status_v2_39_1.md`
- `cycle_audit_v2_39_1.json`

## Practical commands

```bash
./.venv/bin/python scripts/run_continuous_quant_research_v2_39_1.py doctor
./.venv/bin/python scripts/run_continuous_quant_research_v2_39_1.py cycle --run-discovery --max-jobs 50
./.venv/bin/python scripts/run_continuous_quant_research_v2_39_1.py review-queue
./.venv/bin/python scripts/run_continuous_quant_research_v2_39_1.py explain --entity-id STRATEGY:<id>
```

Research compliance is not applied at this stage. Broker submission and automatic live/champion promotion remain disabled.
