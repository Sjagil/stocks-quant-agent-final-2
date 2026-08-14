#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from stocks.integrations import (
    IntegrationRegistry,
    IntegrationRunner,
)
from stocks.research.discovery_screener import (
    DiscoveryPolicy,
    canonicalize_reference_candidates,
)
from stocks.research.validated_strategy_registry import (
    write_validated_strategy_registry,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--as-of",
        default=None,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=150,
    )

    args = parser.parse_args()

    (
        strategy_frame,
        strategy_audit,
        strategy_path,
    ) = (
        write_validated_strategy_registry(
            ROOT
        )
    )

    policy = DiscoveryPolicy.load(
        ROOT
        / "config"
        / "discovery_screener.json"
    )

    if (
        args.limit
        > policy.maximum_candidates
    ):
        raise ValueError(
            "requested limit exceeds "
            "canonical policy maximum"
        )

    payload = {
        "limit": int(
            args.limit
        )
    }

    if args.as_of:
        payload[
            "as_of"
        ] = args.as_of

    registry = (
        IntegrationRegistry.load(
            ROOT
            / "config"
            / "integrations.yaml"
        )
    )

    response = (
        IntegrationRunner(
            registry
        ).run(
            "stocks_reference",
            "screener_candidates",
            payload,
            raise_on_error=True,
        )
    )

    if not response.ok:
        raise RuntimeError(
            response.error
            or (
                "reference screener "
                "failed"
            )
        )

    artifact_path = None

    for artifact in (
        response.artifacts
    ):
        candidate = Path(
            artifact.path
        )

        if (
            candidate.name
            == (
                "stocks_reference_"
                "screener_candidates.json"
            )
        ):
            artifact_path = (
                candidate
            )
            break

    if artifact_path is None:
        raise ValueError(
            "reference screener "
            "artifact missing"
        )

    if not (
        artifact_path.is_file()
    ):
        raise FileNotFoundError(
            artifact_path
        )

    raw = json.loads(
        artifact_path.read_text(
            encoding="utf-8"
        )
    )

    frame, audit = (
        canonicalize_reference_candidates(
            raw,
            policy,
        )
    )

    audit[
        "validated_strategy_count"
    ] = int(
        (
            strategy_frame[
                "promotion_stage"
            ]
            == "FINALIST_CANDIDATE"
        ).sum()
    )

    audit[
        "validated_hypothesis_ids"
    ] = (
        strategy_frame.loc[
            strategy_frame[
                "promotion_stage"
            ]
            == "FINALIST_CANDIDATE",
            "hypothesis_id",
        ]
        .astype(str)
        .tolist()
    )

    audit[
        "strategy_registry"
    ] = str(
        strategy_path
    )

    audit[
        "strategy_registry_live_ready"
    ] = bool(
        strategy_audit[
            "live_ready"
        ]
    )

    output_root = (
        ROOT
        / "artifacts"
        / "research_runtime"
        / "discovery_screener"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        output_root
        / "candidates.csv"
    )

    parquet_path = (
        output_root
        / "candidates.parquet"
    )

    audit_path = (
        output_root
        / "audit.json"
    )

    frame.to_csv(
        csv_path,
        index=False,
    )

    frame.to_parquet(
        parquet_path,
        index=False,
    )

    audit_path.write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "VALIDATED_STRATEGIES",
        audit[
            "validated_strategy_count"
        ],
    )

    print(
        "CANDIDATES",
        audit[
            "candidate_count"
        ],
    )

    print(
        "CORE",
        audit[
            "core_count"
        ],
    )

    print(
        "GEMS",
        audit[
            "gem_count"
        ],
    )

    print(
        "TACTICAL_PRIMARY",
        audit[
            "tactical_primary_count"
        ],
    )

    print(
        "TACTICAL_TAGGED",
        audit[
            "tactical_tag_count"
        ],
    )

    print(
        "WATCHLIST",
        audit[
            "watchlist_count"
        ],
    )

    print()

    if not frame.empty:
        columns = [
            "symbol",
            "asset_type",
            "lane",
            "classification",
            "total_score",
            "fundamental_score",
            "technical_score",
            "market_cap",
            "daily_return",
            "shariah_status",
        ]

        print(
            frame[
                columns
            ]
            .head(
                50
            )
            .to_string(
                index=False
            )
        )

    print()

    print(
        "ARTIFACT_ROOT",
        output_root,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
