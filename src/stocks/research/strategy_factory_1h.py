from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from stocks.data.canonical import canonicalize_ohlcv
from stocks.intelligence_agent.strategy_combo_research_lab import (
    FeatureCache,
    StrategySpec,
    one_factor_and_sampled_grid,
    params_valid,
    strategy_registry,
)


PRIMARY_TIMEFRAME = "1h"

PARAMETER_BASIS = (
    "BAR_NATIVE_1H"
)

BLOCKED_1H_V1 = frozenset(
    {
        "triple_screen",
        "spy_month_end",
        "tlt_thursday_dip",
    }
)


@dataclass(frozen=True)
class OneHourHypothesis:
    hypothesis_id: str
    strategy: str
    family: str
    horizon: str
    params: dict
    primary_timeframe: str = (
        PRIMARY_TIMEFRAME
    )
    parameter_basis: str = (
        PARAMETER_BASIS
    )
    source_engine: str = (
        "strategy_combo_lab_v2"
    )
    execution_authority: str = (
        "NONE"
    )

    def as_record(
        self,
    ) -> dict:
        result = asdict(
            self
        )

        result[
            "params_json"
        ] = json.dumps(
            self.params,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

        result.pop(
            "params",
            None,
        )

        return result


def eligible_1h_specs(
) -> tuple[
    StrategySpec,
    ...,
]:
    result = []

    for spec in (
        strategy_registry()
    ):
        if (
            spec.policy_status
            != "LONG_ONLY_GO"
        ):
            continue

        if (
            spec.name
            in BLOCKED_1H_V1
        ):
            continue

        result.append(
            spec
        )

    return tuple(
        result
    )


def stable_seed(
    strategy: str,
    seed: int,
) -> int:
    payload = (
        f"{seed}|{strategy}"
        .encode(
            "utf-8"
        )
    )

    digest = (
        hashlib.sha256(
            payload
        )
        .hexdigest()
    )

    return (
        int(
            digest[:8],
            16,
        )
        % 2_147_483_647
    )


def hypothesis_id(
    strategy: str,
    params: Mapping,
) -> str:
    payload = json.dumps(
        {
            "strategy": strategy,
            "params": dict(
                params
            ),
            "timeframe": (
                PRIMARY_TIMEFRAME
            ),
            "parameter_basis": (
                PARAMETER_BASIS
            ),
        },
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        default=str,
    )

    return (
        hashlib.sha256(
            payload.encode(
                "utf-8"
            )
        )
        .hexdigest()[:20]
    )


def generate_hypotheses(
    *,
    max_variants_per_strategy: int,
    seed: int,
) -> list[
    OneHourHypothesis
]:
    if (
        max_variants_per_strategy
        <= 0
    ):
        raise ValueError(
            "max_variants_per_strategy "
            "must be positive"
        )

    output = []

    for spec in (
        eligible_1h_specs()
    ):
        variants = (
            one_factor_and_sampled_grid(
                spec.default_params,
                spec.choices,
                "long",
                False,
                int(
                    max_variants_per_strategy
                ),
                stable_seed(
                    spec.name,
                    seed,
                ),
            )
        )

        seen = set()

        for raw_params in (
            variants
        ):
            params = dict(
                raw_params
            )

            if not params_valid(
                spec.name,
                params,
            ):
                continue

            marker = json.dumps(
                params,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
                default=str,
            )

            if marker in seen:
                continue

            seen.add(
                marker
            )

            output.append(
                OneHourHypothesis(
                    hypothesis_id=(
                        hypothesis_id(
                            spec.name,
                            params,
                        )
                    ),
                    strategy=(
                        spec.name
                    ),
                    family=(
                        spec.family
                    ),
                    horizon=(
                        spec.horizon
                    ),
                    params=params,
                )
            )

    ids = [
        item.hypothesis_id
        for item in output
    ]

    if (
        len(ids)
        != len(
            set(ids)
        )
    ):
        raise ValueError(
            "duplicate hypothesis ids"
        )

    return output


def prepare_one_hour_frame(
    frame: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    work = (
        canonicalize_ohlcv(
            frame
        )
        .reset_index()
    )

    time_column = None

    for candidate in (
        "timestamp",
        "datetime",
        "date",
        "timestamp_utc",
    ):
        if candidate in (
            work.columns
        ):
            time_column = (
                candidate
            )
            break

    if time_column is None:
        raise ValueError(
            f"{symbol}: canonical "
            "timestamp column missing"
        )

    work = work.rename(
        columns={
            time_column: (
                "date"
            )
        }
    )

    work[
        "date"
    ] = pd.to_datetime(
        work[
            "date"
        ],
        utc=True,
        errors="coerce",
    )

    work = (
        work.dropna(
            subset=[
                "date",
                "open",
                "high",
                "low",
                "close",
            ]
        )
        .sort_values(
            "date"
        )
        .drop_duplicates(
            "date",
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    if (
        work[
            "date"
        ]
        .duplicated()
        .any()
    ):
        raise ValueError(
            f"{symbol}: duplicate "
            "1h timestamps"
        )

    work[
        "symbol"
    ] = (
        symbol.upper()
    )

    if (
        "volume"
        not in work
    ):
        work[
            "volume"
        ] = np.nan

    return work[
        [
            "symbol",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].copy()


def build_feature_caches(
    frames: Mapping[
        str,
        pd.DataFrame,
    ],
) -> dict[
    str,
    FeatureCache,
]:
    return {
        symbol: (
            FeatureCache(
                frame
            )
        )
        for symbol, frame
        in frames.items()
    }


def evaluate_hypothesis(
    hypothesis: OneHourHypothesis,
    spec: StrategySpec,
    frames: Mapping[
        str,
        pd.DataFrame,
    ],
    caches: Mapping[
        str,
        FeatureCache,
    ],
) -> pd.DataFrame:
    rows = []

    for (
        symbol,
        frame,
    ) in frames.items():
        trades = (
            spec.builder(
                frame,
                caches[
                    symbol
                ],
                hypothesis.params,
            )
        )

        if (
            len(trades)
            == 0
        ):
            continue

        part = pd.DataFrame(
            {
                "hypothesis_id": (
                    hypothesis
                    .hypothesis_id
                ),
                "strategy": (
                    hypothesis
                    .strategy
                ),
                "family": (
                    hypothesis
                    .family
                ),
                "symbol": symbol,
                "entry_time": (
                    pd.to_datetime(
                        trades.entry_dates,
                        utc=True,
                    )
                ),
                "exit_time": (
                    pd.to_datetime(
                        trades.exit_dates,
                        utc=True,
                    )
                ),
                "gross_return": (
                    np.asarray(
                        trades.gross_returns,
                        dtype=float,
                    )
                ),
                "score": (
                    np.asarray(
                        trades.scores,
                        dtype=float,
                    )
                ),
                "duration_bars": (
                    np.asarray(
                        trades.durations,
                        dtype=int,
                    )
                ),
                "forced": (
                    np.asarray(
                        trades.forced,
                        dtype=bool,
                    )
                ),
            }
        )

        finite = np.isfinite(
            part[
                "gross_return"
            ]
        )

        part = part.loc[
            finite
        ]

        if not part.empty:
            rows.append(
                part
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "hypothesis_id",
                "strategy",
                "family",
                "symbol",
                "entry_time",
                "exit_time",
                "gross_return",
                "score",
                "duration_bars",
                "forced",
            ]
        )

    return (
        pd.concat(
            rows,
            ignore_index=True,
        )
        .sort_values(
            [
                "entry_time",
                "symbol",
            ]
        )
        .reset_index(
            drop=True
        )
    )


def net_returns_from_gross(
    gross_returns,
    *,
    cost_bps_per_side: float,
) -> np.ndarray:
    gross = np.asarray(
        gross_returns,
        dtype=float,
    )

    cost = (
        float(
            cost_bps_per_side
        )
        / 10_000.0
    )

    if (
        cost < 0
        or cost >= 1
    ):
        raise ValueError(
            "invalid cost_bps_per_side"
        )

    return (
        (
            1.0
            + gross
        )
        * (
            1.0
            - cost
        )
        / (
            1.0
            + cost
        )
        - 1.0
    )


def trade_metrics(
    trades: pd.DataFrame,
    *,
    cost_bps_per_side: float,
) -> dict:
    if trades.empty:
        return {
            "trades": 0,
            "gross_expectancy": (
                math.nan
            ),
            "net_expectancy": (
                math.nan
            ),
            "net_expectancy_bps": (
                math.nan
            ),
            "median_net_return": (
                math.nan
            ),
            "profit_factor": (
                math.nan
            ),
            "win_rate": (
                math.nan
            ),
            "worst_trade": (
                math.nan
            ),
            "p10_trade": (
                math.nan
            ),
            "return_std": (
                math.nan
            ),
            "expectancy_t_proxy": (
                math.nan
            ),
            "median_duration_bars": (
                math.nan
            ),
            "forced_ratio": (
                math.nan
            ),
            "cost_bps_per_side": (
                float(
                    cost_bps_per_side
                )
            ),
        }

    gross = pd.to_numeric(
        trades[
            "gross_return"
        ],
        errors="coerce",
    ).to_numpy(
        dtype=float
    )

    finite = np.isfinite(
        gross
    )

    gross = gross[
        finite
    ]

    if (
        gross.size
        == 0
    ):
        return trade_metrics(
            trades.iloc[
                0:0
            ],
            cost_bps_per_side=(
                cost_bps_per_side
            ),
        )

    net = (
        net_returns_from_gross(
            gross,
            cost_bps_per_side=(
                cost_bps_per_side
            ),
        )
    )

    gains = float(
        net[
            net > 0
        ].sum()
    )

    losses = float(
        -net[
            net < 0
        ].sum()
    )

    if losses > 0:
        profit_factor = (
            gains
            / losses
        )
    elif gains > 0:
        profit_factor = (
            math.inf
        )
    else:
        profit_factor = 0.0

    std = (
        float(
            np.std(
                net,
                ddof=1,
            )
        )
        if len(net) > 1
        else math.nan
    )

    expectancy = float(
        np.mean(
            net
        )
    )

    if (
        len(net) > 1
        and math.isfinite(
            std
        )
        and std > 0
    ):
        t_proxy = (
            expectancy
            / (
                std
                / math.sqrt(
                    len(net)
                )
            )
        )
    else:
        t_proxy = (
            math.nan
        )

    duration = (
        pd.to_numeric(
            trades.loc[
                finite,
                "duration_bars",
            ],
            errors="coerce",
        )
        .to_numpy(
            dtype=float
        )
    )

    forced = (
        trades.loc[
            finite,
            "forced",
        ]
        .astype(
            bool
        )
        .to_numpy()
    )

    return {
        "trades": int(
            len(net)
        ),
        "gross_expectancy": float(
            np.mean(
                gross
            )
        ),
        "net_expectancy": (
            expectancy
        ),
        "net_expectancy_bps": (
            expectancy
            * 10_000.0
        ),
        "median_net_return": float(
            np.median(
                net
            )
        ),
        "profit_factor": float(
            profit_factor
        ),
        "win_rate": float(
            np.mean(
                net > 0
            )
        ),
        "worst_trade": float(
            np.min(
                net
            )
        ),
        "p10_trade": float(
            np.quantile(
                net,
                0.10,
            )
        ),
        "return_std": (
            std
        ),
        "expectancy_t_proxy": float(
            t_proxy
        ),
        "median_duration_bars": (
            float(
                np.nanmedian(
                    duration
                )
            )
            if duration.size
            else math.nan
        ),
        "forced_ratio": (
            float(
                np.mean(
                    forced
                )
            )
            if forced.size
            else math.nan
        ),
        "cost_bps_per_side": float(
            cost_bps_per_side
        ),
    }


def utc_timestamp(
    value,
) -> pd.Timestamp:
    result = pd.Timestamp(
        value
    )

    if (
        result.tzinfo
        is None
    ):
        return (
            result.tz_localize(
                "UTC"
            )
        )

    return (
        result.tz_convert(
            "UTC"
        )
    )


def contained_trades(
    trades: pd.DataFrame,
    period: list[
        str
    ],
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    start = utc_timestamp(
        period[0]
    )

    end = utc_timestamp(
        period[1]
    )

    entry = pd.to_datetime(
        trades[
            "entry_time"
        ],
        utc=True,
    )

    exit_time = pd.to_datetime(
        trades[
            "exit_time"
        ],
        utc=True,
    )

    mask = (
        (entry >= start)
        & (exit_time <= end)
    )

    return trades.loc[
        mask
    ].copy()


def period_metrics(
    trades: pd.DataFrame,
    period: list[
        str
    ],
    *,
    cost_bps_per_side: float,
) -> dict:
    return trade_metrics(
        contained_trades(
            trades,
            period,
        ),
        cost_bps_per_side=(
            cost_bps_per_side
        ),
    )


def hypotheses_frame(
    hypotheses: list[
        OneHourHypothesis
    ],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            hypothesis
            .as_record()
            for hypothesis
            in hypotheses
        ]
    )
