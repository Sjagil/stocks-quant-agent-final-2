# Contextual Discovery v2

Run from `stocks-quant-agent-final-2` root:

```bash
python /path/to/stocks_contextual_discovery_v2/apply_upgrade.py
python -m pytest -q tests/test_contextual_discovery.py -vv
python -m pytest -q
python -m pip check
python -m compileall -q src scripts
git diff --check
python scripts/run_contextual_discovery.py --as-of 2026-08-14 --limit 150
```

Then commit only after the full suite and runtime pass:

```bash
git add config/contextual_discovery.json config/integrations.yaml scripts/workers/stocks_context_reference_worker.py scripts/run_contextual_discovery.py src/stocks/research/contextual_discovery.py tests/test_contextual_discovery.py
git diff --cached --check
git diff --cached --stat
git commit -m "Add macro and SEC contextual discovery layer"
git push origin feature/alpha-factory-v1
```
