# v2.39.3 Practical Evidence Production

v2.39.3 turns v2.39.2's evidence gaps into executable research work. It does not relax promotion gates and does not grant execution authority.

## Goals

- Produce observation-level OOS evidence instead of relabeling aggregate summaries.
- Reconstruct the existing 1h strategy-factory test folds only when the replay reproduces stored test metrics.
- Count overlapping cross-asset trades conservatively using temporal event clusters.
- Require at least 60 effective OOS observations and 60 raw OOS trades by default.
- Re-run 1x / 1.5x / 2x / 3x cost stress on the same OOS observations.
- Bind every evidence record to stable provenance and make ingestion idempotent.
- Recompute v2.39.2 quality/readiness immediately after evidence ingestion.
- Never auto-promote a champion and never call a broker.

## Factory replay

The preferred adapter is the existing `strategy_factory_1h` pipeline. The original pipeline selects candidates using train/validation information before it computes test metrics. v2.39.3 reads the exact selected folds and reconstructs the test windows from the same local 1h data.

Because the legacy factory audit did not persist every fold parameter, v2.39.3 does not trust a reconstructed fold blindly. For every selected fold it recomputes:

- test trade count
- test net expectancy bps
- test profit factor

These must match the original `fold_selected.csv` within configured tolerances. A mismatch yields `REPLAY_PROVENANCE_MISMATCH` and no evidence is ingested.

## Effective observations

Raw trades can overlap across assets and holding windows. v2.39.3 therefore records both:

- `raw_trades`
- `effective_observations`

The effective count uses conservative temporal interval clustering: all concurrently open trades are one observation cluster. The promotion sample gate uses the effective count.

## Cost stress

Cost stress is produced on the same OOS trade returns at 1.0x, 1.5x, 2.0x and 3.0x of the historical baseline execution-cost contract. The producer also cross-checks the canonical v2.33 trade-return stress and v2.36 mean-edge stress primitives. A scenario only receives `passed=true` when both its expectancy is positive and the effective OOS sample requirement is satisfied.

## Evidence time

Evidence `as_of` is the latest actual OOS exit timestamp, not the wall-clock time when the producer ran. Replaying old data therefore cannot make stale evidence appear fresh.

## External observation-grade adapter

For strategies not replayable through the 1h factory, `produce-from-observations` accepts an observation-level CSV/Parquet plus a provenance JSON. The provenance must include:

```json
{
  "selection_protocol": "PURGED_WALK_FORWARD",
  "selected_without_test_labels": true,
  "label_overlap_checked": true,
  "source_engine": "your_engine",
  "data_as_of": "2026-08-24T00:00:00Z"
}
```

Aggregate summary files are rejected because they do not contain entry/exit level observations.

## CLI

```bash
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py doctor
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py plan
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py audit-inputs --entity-id STRATEGY:<id>
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py produce --entity-id STRATEGY:<id>
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py produce-due --max-entities 5
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py status
```

External observation input:

```bash
./.venv/bin/python scripts/run_research_evidence_production_v2_39_3.py \
  produce-from-observations \
  --entity-id STRATEGY:<id> \
  --file oos_observations.csv \
  --provenance provenance.json \
  --base-cost-bps-per-side 3
```

## Outputs

Outputs live under the existing continuous-research runtime:

`artifacts/research_runtime/continuous_quant_research_v2_39/evidence_production_v2_39_3/`

Per entity:

- `input_audit.json`
- `provenance.json`
- `oos_observations.csv`
- `oos_evidence.json`
- `cost_stress_scenarios.csv`
- `cost_evidence.json`
- `production_result.json`

Global:

- `latest_production_summary.json`
- `production_summary.csv`

## Safety

- `execution_authority = NONE`
- `broker_submission_enabled = false`
- `automatic_live_promotion = false`
- `automatic_champion_promotion = false`
- no order submission calls
- no broker calls
- champion approval remains governed by v2.39.2 and manual review
