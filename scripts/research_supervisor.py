from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from stocks.research.supervisor import ResearchSupervisor


ROOT = Path(__file__).resolve().parents[1]


def parse_symbols(value: str) -> tuple[str, ...]:
    return tuple(
        item.strip().upper()
        for item in value.split(",")
        if item.strip()
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    once = sub.add_parser("once")

    once.add_argument(
        "--symbols",
        default="AAPL,AMD,MSFT,NVDA,SPY,QQQ,GLD,SLV,CPER",
    )

    once.add_argument("--optimize", action="store_true")
    once.add_argument("--external", action="store_true")
    once.add_argument("--heavy", action="store_true")

    loop = sub.add_parser("loop")

    loop.add_argument(
        "--symbols",
        default="AAPL,AMD,MSFT,NVDA,SPY,QQQ,GLD,SLV,CPER",
    )

    loop.add_argument(
        "--interval-seconds",
        type=int,
        default=900,
    )

    loop.add_argument(
        "--external-every",
        type=int,
        default=4,
    )

    loop.add_argument(
        "--heavy-every",
        type=int,
        default=96,
    )

    return parser


def run_once(args) -> int:
    supervisor = ResearchSupervisor(ROOT)

    result = supervisor.run_cycle(
        parse_symbols(args.symbols),
        optimize=args.optimize,
        external=args.external,
        heavy=args.heavy,
    )

    print(
        json.dumps(
            {
                "artifact": result["artifact"],
                "symbols": list(result["symbols"]),
                "external": bool(result["external"]),
                "heavy": bool(result["heavy"]),
            },
            indent=2,
        )
    )

    return 0


def run_loop(args) -> int:
    supervisor = ResearchSupervisor(ROOT)

    cycle = 0

    while True:
        cycle += 1

        external = (
            args.external_every > 0
            and cycle % args.external_every == 0
        )

        heavy = (
            args.heavy_every > 0
            and cycle % args.heavy_every == 0
        )

        result = supervisor.run_cycle(
            parse_symbols(args.symbols),
            optimize=heavy,
            external=external,
            heavy=heavy,
        )

        print(
            json.dumps(
                {
                    "cycle": cycle,
                    "artifact": result["artifact"],
                    "external": external,
                    "heavy": heavy,
                }
            ),
            flush=True,
        )

        time.sleep(max(60, args.interval_seconds))


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "once":
        return run_once(args)

    return run_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
