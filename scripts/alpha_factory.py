from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from stocks.research import AlphaFactory, AlphaHypothesis


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    plan = sub.add_parser("plan")
    plan.add_argument("--symbols", required=True)
    plan.add_argument("--family", default="active_swing")
    plan.add_argument("--thesis", required=True)
    plan.add_argument(
        "--timeframes",
        default="15m,1h,2h,4h,1d,1w",
    )

    loop = sub.add_parser("loop")
    loop.add_argument("--seconds", type=int, default=300)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    factory = AlphaFactory(ROOT)

    if args.command == "status":
        status = factory.capability_status()
        factory.write_status()
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0 if status["status"] == "OK" else 1

    if args.command == "plan":
        hypothesis = AlphaHypothesis(
            family=args.family,
            thesis=args.thesis,
            symbols=tuple(
                x.strip().upper()
                for x in args.symbols.split(",")
                if x.strip()
            ),
            timeframes=tuple(
                x.strip()
                for x in args.timeframes.split(",")
                if x.strip()
            ),
        )
        plan = factory.create_plan(hypothesis)
        path = factory.write_plan(plan)
        payload = plan.as_dict()
        payload["artifact"] = str(path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "loop":
        while True:
            status = factory.capability_status()
            path = factory.write_status()
            print(
                json.dumps(
                    {
                        "status": status["status"],
                        "available": status["available"],
                        "total": status["total"],
                        "artifact": str(path),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            time.sleep(max(60, args.seconds))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
