# v2.39 Continuous Quant Research Engine

v2.39 turns the existing research scripts into a persistent, restart-safe research control plane.

## Immediate use

```bash
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py doctor
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py init
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py cycle --run-discovery --max-jobs 50
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py status
```

For a foreground continuous process:

```bash
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py watch --interval-seconds 3600 --discovery-every 24
```

## Persistent state

`artifacts/research_runtime/continuous_quant_research_v2_39/research.db` stores entities, evidence, jobs, attempts, recommendations, cycles, and manual role changes. SQLite WAL + FULL synchronous mode are used.

## Safety

- research roles never grant execution authority;
- CHAMPION is a research role only;
- automatic live promotion is disabled;
- role promotion to CHAMPION is manual through `approve-role`;
- severe drift/decay can recommend deactivation but never submit an order;
- execution authority remains NONE.

## Practical evidence routes

- existing candidate registry is synchronized every cycle;
- v2.37 shadow feedback can be ingested from JSON/JSONL/CSV;
- arbitrary structured research evaluation evidence can be ingested;
- feature/data drift can be computed directly from two CSV panels using canonical v2.31 PSI/JS logic;
- a daily discovery refresh can call the existing allowlisted `scripts/run_parallel_research.py`.

## Experiment registry

Register concrete experiments and attach their results without losing history:

```bash
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py experiment --entity-id STRATEGY:abc --type COST_STRESS --hypothesis "edge survives 2x costs"
./.venv/bin/python scripts/run_continuous_quant_research_v2_39.py experiment-result --experiment-id <id> --status SUCCEEDED --result-ref artifacts/.../result.json
```

`CHAMPION` is never assigned automatically. `approve-role` is the only v2.39 path that can set that research role.
