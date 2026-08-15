from pathlib import Path
import shutil
ROOT=Path.cwd(); BUNDLE=Path(__file__).resolve().parent
for p in [ROOT/'config/integrations.yaml',ROOT/'src/stocks/research',ROOT/'scripts/workers']:
    if not p.exists(): raise SystemExit(f'Run from stocks-quant-agent-final-2 root; missing {p}')
for rel in ['config/contextual_discovery.json','scripts/workers/stocks_context_reference_worker.py','scripts/run_contextual_discovery.py','src/stocks/research/contextual_discovery.py','tests/test_contextual_discovery.py']:
    src=BUNDLE/rel; dst=ROOT/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); print('COPIED',rel)
path=ROOT/'config/integrations.yaml'; text=path.read_text(encoding='utf-8')
if 'stocks_context_reference:' not in text:
    anchor='\n  finrl:\n'
    if anchor not in text: raise SystemExit('Could not find finrl insertion anchor')
    block='''\n  stocks_context_reference:\n    enabled: true\n    kind: isolated_python\n    python: "${STOCKS_REFERENCE_PYTHON:-.venvs/stocks/bin/python}"\n    worker: scripts/workers/stocks_context_reference_worker.py\n    repo: references/Stocks\n    distributions: []\n    imports: []\n    capabilities: [health, catalog, discovery_context]\n    pass_env:\n      - EODHD_API_KEY\n      - EOD_API_KEY\n      - EODHISTORICALDATA_API_KEY\n    timeout_seconds: 900\n'''
    path.write_text(text.replace(anchor,block+anchor,1),encoding='utf-8'); print('UPDATED config/integrations.yaml')
