from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.integrations import IntegrationRegistry, IntegrationRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one configured isolated research integration action")
    parser.add_argument("integration")
    parser.add_argument("action")
    parser.add_argument("--config", type=Path, default=Path("config/integrations.yaml"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--payload-json", default="{}")
    group.add_argument("--payload-file", type=Path)
    parser.add_argument("--strict", action="store_true", help="Raise/exit when the worker is unavailable or fails")
    args = parser.parse_args()

    if args.payload_file:
        payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
    else:
        payload = json.loads(args.payload_json)
    if not isinstance(payload, dict):
        raise SystemExit("payload must be a JSON object")

    registry = IntegrationRegistry.load(args.config)
    response = IntegrationRunner(registry).run(
        args.integration,
        args.action,
        payload,
        raise_on_error=args.strict,
    )
    print(json.dumps(response.to_dict(), indent=2, default=str))
    if args.strict and not response.ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
