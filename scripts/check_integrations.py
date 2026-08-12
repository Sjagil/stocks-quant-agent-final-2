from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.integrations import IntegrationRegistry, IntegrationRunner, IntegrationState


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe isolated external research integrations")
    parser.add_argument("--config", type=Path, default=Path("config/integrations.yaml"))
    parser.add_argument("--catalog", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when any enabled optional integration is unavailable")
    args = parser.parse_args()

    registry = IntegrationRegistry.load(args.config)
    runner = IntegrationRunner(registry)
    failures = 0
    required_failures = 0
    for name in registry.names(enabled_only=True):
        response = runner.run(name, "catalog" if args.catalog else "health")
        print(json.dumps(response.to_dict(), indent=2, default=str))
        if response.state is not IntegrationState.OK:
            failures += 1
            if registry.get(name).required and not response.ok:
                required_failures += 1
    if required_failures or (args.strict and failures):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
