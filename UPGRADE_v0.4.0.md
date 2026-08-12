# Upgrade to v0.4.0

This release is designed to overlay an existing `stocks-quant-agent-final-2` working directory **without deleting** local data, `.env`, `.venvs/` or `references/`.

## What changes

- Adds `config/integrations.yaml`.
- Adds the isolated integration contract/registry/runner package.
- Adds VeighNa/Qlib/FinRL/MoonDev/Nautilus workers.
- Adds canonical market-data schema and refactors EODHD download/split normalization onto it.
- Updates the RL data validator to use canonical data validation.
- Updates package version to `0.4.0` and makes PyYAML/PyArrow core dependencies.
- Keeps `vnpy_ib` reference-only; it is not reinstalled into `.venvs/vnpy`.

## Safe overlay

Use the separate patch bundle from the chat for the easiest upgrade. Its apply script backs up every touched target file before copying the patch.

After the overlay:

```bash
cd ~/Downloads/stocks-quant-agent-final-2
source .venv/bin/activate
python -m pip install -e '.[rl,dev]'
python -m pip check
python -m pytest -q
python scripts/check_integrations.py
```

`check_integrations.py` is non-strict by default so an optional unavailable Nautilus/FinRL environment is reported but does not fail the command. Use `--strict` when you intentionally require every enabled integration to be healthy.
