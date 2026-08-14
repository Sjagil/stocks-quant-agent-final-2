from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CANDIDATE_CLASSES = frozenset(
    {
        "HIGH_POTENTIAL",
        "WATCHLIST",
    }
)


@dataclass(
    frozen=True
)
class DiscoveryPolicy:
    gem_market_cap_ceiling_usd: float
    tactical_min_technical_score: float
    tactical_min_absolute_daily_return: float
    maximum_candidates: int

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "DiscoveryPolicy":
        raw = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if (
            raw.get(
                "schema"
            )
            != (
                "candidate_discovery_"
                "policy_v1"
            )
        ):
            raise ValueError(
                "invalid discovery policy "
                "schema"
            )

        result = cls(
            gem_market_cap_ceiling_usd=(
                float(
                    raw[
                        "gem_market_cap_"
                        "ceiling_usd"
                    ]
                )
            ),
            tactical_min_technical_score=(
                float(
                    raw[
                        "tactical_min_"
                        "technical_score"
                    ]
                )
            ),
            tactical_min_absolute_daily_return=(
                float(
                    raw[
                        "tactical_min_"
                        "absolute_daily_return"
                    ]
                )
            ),
            maximum_candidates=int(
                raw[
                    "maximum_candidates"
                ]
            ),
        )

        if (
            result
            .gem_market_cap_ceiling_usd
            <= 0
        ):
            raise ValueError(
                "invalid gem market-cap "
                "ceiling"
            )

        if not (
            0
            < result.maximum_candidates
            <= 500
        ):
            raise ValueError(
                "invalid candidate maximum"
            )

        return result


def _finite(
    value: Any,
    *,
    field: str,
    allow_none: bool = False,
) -> float | None:
    if value in (
        None,
        "",
    ):
        if allow_none:
            return None

        raise ValueError(
            f"{field}: value missing"
        )

    result = float(
        value
    )

    if not math.isfinite(
        result
    ):
        raise ValueError(
            f"{field}: non-finite value"
        )

    return result


def _validate_timestamp(
    value: Any,
    *,
    decision_time: pd.Timestamp,
    field: str,
) -> None:
    if value in (
        None,
        "",
    ):
        return

    timestamp = pd.to_datetime(
        value,
        utc=True,
        errors="coerce",
    )

    if pd.isna(
        timestamp
    ):
        raise ValueError(
            f"{field}: invalid timestamp"
        )

    if timestamp > decision_time:
        raise ValueError(
            f"{field}: future information"
        )


def canonicalize_reference_candidates(
    payload: dict[str, Any],
    policy: DiscoveryPolicy,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    if (
        payload.get(
            "schema"
        )
        != (
            "stocks_reference_"
            "screener_candidates_v1"
        )
    ):
        raise ValueError(
            "invalid reference screener "
            "schema"
        )

    if (
        payload.get(
            "execution_authority"
        )
        != "NONE"
        or int(
            payload.get(
                "broker_calls",
                0,
            )
        )
        != 0
        or int(
            payload.get(
                "order_calls",
                0,
            )
        )
        != 0
    ):
        raise ValueError(
            "reference screener attempted "
            "authority escalation"
        )

    decision_time = pd.to_datetime(
        payload[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    screening_date = pd.Timestamp(
        payload[
            "screening_date"
        ]
    ).date()

    rows = []

    seen: set[str] = set()

    for record in (
        payload.get(
            "records"
        )
        or []
    ):
        symbol = str(
            record.get(
                "symbol"
            )
            or ""
        ).strip().upper()

        if not symbol:
            raise ValueError(
                "candidate symbol missing"
            )

        if symbol in seen:
            raise ValueError(
                f"duplicate candidate: "
                f"{symbol}"
            )

        seen.add(
            symbol
        )

        classification = str(
            record.get(
                "classification"
            )
            or ""
        )

        if (
            classification
            not in CANDIDATE_CLASSES
        ):
            raise ValueError(
                f"{symbol}: invalid "
                "candidate classification"
            )

        if (
            record.get(
                "rejection_reasons"
            )
            or []
        ):
            raise ValueError(
                f"{symbol}: candidate has "
                "hard rejection reasons"
            )

        if (
            record.get(
                "execution_authority"
            )
            != "NONE"
        ):
            raise ValueError(
                f"{symbol}: execution "
                "authority escalation"
            )

        timestamps = dict(
            record.get(
                "data_timestamps"
            )
            or {}
        )

        for field in (
            "price_source_timestamp",
            "fundamental_available_at",
            "shariah_screened_at",
        ):
            _validate_timestamp(
                timestamps.get(
                    field
                ),
                decision_time=(
                    decision_time
                ),
                field=(
                    f"{symbol}.{field}"
                ),
            )

        price_session = (
            timestamps.get(
                "price_session"
            )
        )

        if price_session:
            session_date = (
                pd.Timestamp(
                    price_session
                )
                .date()
            )

            if (
                session_date
                > screening_date
            ):
                raise ValueError(
                    f"{symbol}: future "
                    "price session"
                )

        total_score = _finite(
            record.get(
                "total_score"
            ),
            field=(
                f"{symbol}.total_score"
            ),
        )

        fundamental_score = (
            _finite(
                record.get(
                    "fundamental_score"
                ),
                field=(
                    f"{symbol}."
                    "fundamental_score"
                ),
            )
        )

        technical_score = _finite(
            record.get(
                "technical_score"
            ),
            field=(
                f"{symbol}.technical_score"
            ),
        )

        liquidity_score = _finite(
            record.get(
                "liquidity_score"
            ),
            field=(
                f"{symbol}.liquidity_score"
            ),
        )

        risk_score = _finite(
            record.get(
                "risk_score"
            ),
            field=(
                f"{symbol}.risk_score"
            ),
        )

        market_cap = _finite(
            record.get(
                "market_cap"
            ),
            field=(
                f"{symbol}.market_cap"
            ),
            allow_none=True,
        )

        daily_return = _finite(
            record.get(
                "daily_return"
            ),
            field=(
                f"{symbol}.daily_return"
            ),
            allow_none=True,
        )

        asset_type = str(
            record.get(
                "asset_type"
            )
            or "UNKNOWN"
        ).upper()

        mover_type = str(
            record.get(
                "mover_type"
            )
            or ""
        ).upper()

        tactical_candidate = (
            (
                bool(
                    mover_type
                )
                or (
                    daily_return
                    is not None
                    and abs(
                        daily_return
                    )
                    >= (
                        policy
                        .tactical_min_absolute_daily_return
                    )
                )
            )
            and (
                technical_score
                >= (
                    policy
                    .tactical_min_technical_score
                )
            )
        )

        if (
            classification
            == "HIGH_POTENTIAL"
        ):
            if (
                asset_type
                == "STOCK"
                and market_cap
                is not None
                and market_cap
                < (
                    policy
                    .gem_market_cap_ceiling_usd
                )
            ):
                lane = "GEM"
            else:
                lane = "CORE"

        elif tactical_candidate:
            lane = "TACTICAL"

        else:
            lane = "WATCHLIST"

        rows.append(
            {
                "symbol": symbol,
                "asset_key": (
                    record.get(
                        "asset_key"
                    )
                ),
                "asset_type": (
                    asset_type
                ),
                "sector": (
                    record.get(
                        "sector"
                    )
                ),
                "industry": (
                    record.get(
                        "industry"
                    )
                ),
                "classification": (
                    classification
                ),
                "lane": lane,
                "core_candidate": (
                    lane
                    == "CORE"
                ),
                "gem_candidate": (
                    lane
                    == "GEM"
                ),
                "tactical_candidate": (
                    tactical_candidate
                ),
                "total_score": (
                    total_score
                ),
                "fundamental_score": (
                    fundamental_score
                ),
                "technical_score": (
                    technical_score
                ),
                "liquidity_score": (
                    liquidity_score
                ),
                "risk_score": (
                    risk_score
                ),
                "macro_score": (
                    record.get(
                        "macro_score"
                    )
                ),
                "market_cap": (
                    market_cap
                ),
                "median_dollar_volume_20d": (
                    record.get(
                        "median_dollar_volume_20d"
                    )
                ),
                "bid_ask_spread_bps": (
                    record.get(
                        "bid_ask_spread_bps"
                    )
                ),
                "daily_return": (
                    daily_return
                ),
                "mover_type": (
                    mover_type
                    or None
                ),
                "shariah_status": (
                    record.get(
                        "shariah_status"
                    )
                ),
                "selection_reasons": (
                    record.get(
                        "selection_reasons"
                    )
                    or []
                ),
                "decision_time": (
                    decision_time
                ),
                "screening_date": (
                    screening_date
                ),
                "source": (
                    "STOCKS_REFERENCE_"
                    "PIT_SCREENER"
                ),
                "strategy_assignment": (
                    "NOT_YET_GENERALIZED"
                ),
                "execution_authority": (
                    "NONE"
                ),
                "broker_calls": 0,
            }
        )

    frame = pd.DataFrame(
        rows
    )

    if len(
        frame
    ) > (
        policy
        .maximum_candidates
    ):
        frame = (
            frame.iloc[
                : (
                    policy
                    .maximum_candidates
                )
            ]
            .copy()
        )

    if not frame.empty:
        lane_rank = {
            "GEM": 0,
            "CORE": 1,
            "TACTICAL": 2,
            "WATCHLIST": 3,
        }

        frame[
            "_lane_rank"
        ] = (
            frame[
                "lane"
            ]
            .map(
                lane_rank
            )
        )

        frame = (
            frame.sort_values(
                [
                    "_lane_rank",
                    "total_score",
                    "technical_score",
                    "symbol",
                ],
                ascending=[
                    True,
                    False,
                    False,
                    True,
                ],
            )
            .drop(
                columns=[
                    "_lane_rank"
                ]
            )
            .reset_index(
                drop=True
            )
        )

    audit = {
        "schema": (
            "canonical_candidate_"
            "discovery_v1"
        ),
        "screening_date": str(
            screening_date
        ),
        "decision_time": (
            decision_time
            .isoformat()
        ),
        "candidate_count": int(
            len(
                frame
            )
        ),
        "core_count": int(
            (
                frame[
                    "lane"
                ]
                == "CORE"
            ).sum()
            if not frame.empty
            else 0
        ),
        "gem_count": int(
            (
                frame[
                    "lane"
                ]
                == "GEM"
            ).sum()
            if not frame.empty
            else 0
        ),
        "tactical_primary_count": int(
            (
                frame[
                    "lane"
                ]
                == "TACTICAL"
            ).sum()
            if not frame.empty
            else 0
        ),
        "tactical_tag_count": int(
            frame[
                "tactical_candidate"
            ].sum()
            if not frame.empty
            else 0
        ),
        "watchlist_count": int(
            (
                frame[
                    "lane"
                ]
                == "WATCHLIST"
            ).sum()
            if not frame.empty
            else 0
        ),
        "validated_strategy_assignment": (
            False
        ),
        "reason": (
            "dynamic-universe "
            "strategy generalization "
            "must run before strategy "
            "assignment"
        ),
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
        "order_calls": 0,
    }

    return (
        frame,
        audit,
    )
