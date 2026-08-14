from pathlib import Path

import pytest

from stocks.research.discovery_screener import (
    DiscoveryPolicy,
    canonicalize_reference_candidates,
)


def policy() -> DiscoveryPolicy:
    return DiscoveryPolicy(
        gem_market_cap_ceiling_usd=(
            25_000_000_000.0
        ),
        tactical_min_technical_score=65.0,
        tactical_min_absolute_daily_return=0.025,
        maximum_candidates=150,
    )


def record(
    symbol,
    *,
    classification,
    market_cap,
    technical=70.0,
    daily_return=0.01,
    mover_type=None,
):
    return {
        "symbol": symbol,
        "asset_key": symbol,
        "asset_type": "STOCK",
        "sector": "TEST",
        "industry": "TEST",
        "classification": classification,
        "total_score": (
            80.0
            if classification
            == "HIGH_POTENTIAL"
            else 65.0
        ),
        "fundamental_score": 70.0,
        "technical_score": technical,
        "liquidity_score": 80.0,
        "risk_score": 70.0,
        "macro_score": 60.0,
        "market_cap": market_cap,
        "median_dollar_volume_20d": (
            10_000_000.0
        ),
        "bid_ask_spread_bps": 20.0,
        "daily_return": daily_return,
        "mover_type": mover_type,
        "shariah_status": (
            "SHARIAH_ELIGIBLE_PIT"
        ),
        "selection_reasons": [],
        "rejection_reasons": [],
        "data_timestamps": {
            "price_session": (
                "2026-08-14"
            ),
            "price_source_timestamp": (
                "2026-08-14T20:00:00+00:00"
            ),
            "fundamental_available_at": (
                "2026-08-01T00:00:00+00:00"
            ),
            "shariah_screened_at": (
                "2026-08-01T00:00:00+00:00"
            ),
        },
        "execution_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def payload(records):
    return {
        "schema": (
            "stocks_reference_"
            "screener_candidates_v1"
        ),
        "screening_date": (
            "2026-08-14"
        ),
        "decision_time": (
            "2026-08-14T23:59:59+00:00"
        ),
        "records": records,
        "execution_authority": "NONE",
        "strategy_authority": "NONE",
        "broker_calls": 0,
        "order_calls": 0,
    }


def test_candidate_lane_routing():
    frame, audit = (
        canonicalize_reference_candidates(
            payload(
                [
                    record(
                        "GEM",
                        classification=(
                            "HIGH_POTENTIAL"
                        ),
                        market_cap=(
                            5_000_000_000.0
                        ),
                    ),
                    record(
                        "CORE",
                        classification=(
                            "HIGH_POTENTIAL"
                        ),
                        market_cap=(
                            100_000_000_000.0
                        ),
                    ),
                    record(
                        "TACT",
                        classification=(
                            "WATCHLIST"
                        ),
                        market_cap=(
                            10_000_000_000.0
                        ),
                        technical=75.0,
                        daily_return=0.05,
                        mover_type="UP",
                    ),
                    record(
                        "WATCH",
                        classification=(
                            "WATCHLIST"
                        ),
                        market_cap=(
                            10_000_000_000.0
                        ),
                        technical=55.0,
                        daily_return=0.005,
                    ),
                ]
            ),
            policy(),
        )
    )

    lanes = dict(
        zip(
            frame[
                "symbol"
            ],
            frame[
                "lane"
            ],
            strict=True,
        )
    )

    assert lanes[
        "GEM"
    ] == "GEM"

    assert lanes[
        "CORE"
    ] == "CORE"

    assert lanes[
        "TACT"
    ] == "TACTICAL"

    assert lanes[
        "WATCH"
    ] == "WATCHLIST"

    assert (
        audit[
            "gem_count"
        ]
        == 1
    )


def test_duplicate_candidate_fails():
    duplicate = record(
        "ABC",
        classification=(
            "HIGH_POTENTIAL"
        ),
        market_cap=(
            5_000_000_000.0
        ),
    )

    with pytest.raises(
        ValueError
    ):
        canonicalize_reference_candidates(
            payload(
                [
                    duplicate,
                    duplicate,
                ]
            ),
            policy(),
        )


def test_authority_escalation_fails():
    raw = payload(
        [
            record(
                "ABC",
                classification=(
                    "HIGH_POTENTIAL"
                ),
                market_cap=(
                    5_000_000_000.0
                ),
            )
        ]
    )

    raw[
        "execution_authority"
    ] = "LIVE"

    with pytest.raises(
        ValueError
    ):
        canonicalize_reference_candidates(
            raw,
            policy(),
        )


def test_future_evidence_fails():
    candidate = record(
        "ABC",
        classification=(
            "HIGH_POTENTIAL"
        ),
        market_cap=(
            5_000_000_000.0
        ),
    )

    candidate[
        "data_timestamps"
    ][
        "fundamental_available_at"
    ] = (
        "2026-08-15T00:00:00+00:00"
    )

    with pytest.raises(
        ValueError
    ):
        canonicalize_reference_candidates(
            payload(
                [
                    candidate
                ]
            ),
            policy(),
        )


def test_policy_file_loads(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "policy.json"
    )

    path.write_text(
        """{
          "schema":
            "candidate_discovery_policy_v1",
          "gem_market_cap_ceiling_usd":
            25000000000,
          "tactical_min_technical_score":
            65,
          "tactical_min_absolute_daily_return":
            0.025,
          "maximum_candidates":
            150
        }""",
        encoding="utf-8",
    )

    result = (
        DiscoveryPolicy.load(
            path
        )
    )

    assert (
        result.maximum_candidates
        == 150
    )
