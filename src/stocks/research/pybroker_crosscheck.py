from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Mapping

import numpy as np
import pandas as pd

from stocks.research.strategy_factory_1h import (
    contained_trades,
    trade_metrics,
)


ENTRY_SIGNAL = (
    "scheduled_entry"
)

EXIT_SIGNAL = (
    "scheduled_exit"
)


def as_utc(
    value,
) -> pd.Timestamp:
    result = pd.Timestamp(
        value
    )

    if result.tzinfo is None:
        return result.tz_localize(
            "UTC"
        )

    return result.tz_convert(
        "UTC"
    )


def as_naive_utc(
    value,
) -> pd.Timestamp:
    return (
        as_utc(
            value
        )
        .tz_localize(
            None
        )
    )


def base_replay_symbol(
    value,
) -> str:
    symbol = str(
        value
    ).upper()

    marker = "__PB"

    if marker in symbol:
        return symbol.split(
            marker,
            1,
        )[0]

    return symbol


def assign_replay_lanes(
    trades: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict,
]:
    if trades.empty:
        return (
            trades.copy(),
            {
                "rollover_count": 0,
                "replay_lane_count": 0,
                "max_replay_lanes_per_symbol": 0,
                "lanes_by_symbol": {},
            },
        )

    required = {
        "symbol",
        "entry_time",
        "exit_time",
    }

    missing = (
        required
        - set(
            trades.columns
        )
    )

    if missing:
        raise ValueError(
            "trade replay input missing "
            f"{sorted(missing)}"
        )

    work = trades.copy()

    work[
        "symbol"
    ] = (
        work[
            "symbol"
        ]
        .astype(str)
        .str.upper()
    )

    work[
        "entry_time"
    ] = pd.to_datetime(
        work[
            "entry_time"
        ],
        utc=True,
        errors="coerce",
    )

    work[
        "exit_time"
    ] = pd.to_datetime(
        work[
            "exit_time"
        ],
        utc=True,
        errors="coerce",
    )

    if (
        work[
            [
                "entry_time",
                "exit_time",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError(
            "invalid replay trade timestamp"
        )

    if (
        work[
            "exit_time"
        ]
        <= work[
            "entry_time"
        ]
    ).any():
        raise ValueError(
            "trade exit must be after entry"
        )

    parts = []

    rollover_count = 0
    lanes_by_symbol = {}

    for symbol, group in (
        work.groupby(
            "symbol",
            sort=True,
        )
    ):
        group = (
            group.sort_values(
                [
                    "entry_time",
                    "exit_time",
                ]
            )
            .copy()
        )

        previous_exit = None

        for row in (
            group.itertuples(
                index=False
            )
        ):
            entry_time = (
                row.entry_time
            )

            exit_time = (
                row.exit_time
            )

            if (
                previous_exit is not None
                and entry_time
                < previous_exit
            ):
                raise ValueError(
                    f"{symbol}: true "
                    "overlapping canonical "
                    "trades detected: "
                    f"entry={entry_time} "
                    f"prior_exit="
                    f"{previous_exit}"
                )

            if (
                previous_exit is not None
                and entry_time
                == previous_exit
            ):
                rollover_count += 1

            previous_exit = (
                exit_time
            )

        lane_last_exit = []

        assigned_lanes = []

        for row in (
            group.itertuples()
        ):
            entry_time = (
                row.entry_time
            )

            exit_time = (
                row.exit_time
            )

            selected_lane = None

            for (
                lane,
                last_exit,
            ) in enumerate(
                lane_last_exit
            ):
                if (
                    last_exit
                    < entry_time
                ):
                    selected_lane = (
                        lane
                    )
                    break

            if (
                selected_lane
                is None
            ):
                selected_lane = len(
                    lane_last_exit
                )

                lane_last_exit.append(
                    exit_time
                )

            else:
                lane_last_exit[
                    selected_lane
                ] = exit_time

            assigned_lanes.append(
                selected_lane
            )

        group[
            "_replay_lane"
        ] = assigned_lanes

        group[
            "_replay_symbol"
        ] = [
            (
                f"{symbol}__PB"
                f"{lane}"
            )
            for lane
            in assigned_lanes
        ]

        lane_count = (
            int(
                group[
                    "_replay_lane"
                ]
                .max()
            )
            + 1
        )

        lanes_by_symbol[
            symbol
        ] = lane_count

        parts.append(
            group
        )

    result = (
        pd.concat(
            parts,
            ignore_index=True,
        )
        .sort_values(
            [
                "entry_time",
                "symbol",
                "_replay_lane",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return (
        result,
        {
            "rollover_count": int(
                rollover_count
            ),
            "replay_lane_count": int(
                sum(
                    lanes_by_symbol.values()
                )
            ),
            "max_replay_lanes_per_symbol": (
                int(
                    max(
                        lanes_by_symbol.values()
                    )
                )
                if lanes_by_symbol
                else 0
            ),
            "lanes_by_symbol": (
                lanes_by_symbol
            ),
        },
    )


def expected_trade_keys(
    trades: pd.DataFrame,
) -> Counter:
    result = Counter()

    if trades.empty:
        return result

    required = {
        "symbol",
        "entry_time",
        "exit_time",
    }

    missing = (
        required
        - set(
            trades.columns
        )
    )

    if missing:
        raise ValueError(
            "expected trade frame missing "
            f"{sorted(missing)}"
        )

    for row in (
        trades.itertuples(
            index=False
        )
    ):
        result[
            (
                str(
                    row.symbol
                ).upper(),
                as_naive_utc(
                    row.entry_time
                ),
                as_naive_utc(
                    row.exit_time
                ),
            )
        ] += 1

    return result


def observed_trade_keys(
    trades: pd.DataFrame,
) -> Counter | None:
    if trades is None:
        return Counter()

    if trades.empty:
        return Counter()

    symbol_column = (
        "symbol"
        if "symbol" in trades
        else None
    )

    entry_column = next(
        (
            column
            for column in (
                "entry_date",
                "entry_time",
            )
            if column in trades
        ),
        None,
    )

    exit_column = next(
        (
            column
            for column in (
                "exit_date",
                "exit_time",
            )
            if column in trades
        ),
        None,
    )

    if (
        symbol_column is None
        or entry_column is None
        or exit_column is None
    ):
        return None

    result = Counter()

    for row in (
        trades[
            [
                symbol_column,
                entry_column,
                exit_column,
            ]
        ]
        .itertuples(
            index=False,
            name=None,
        )
    ):
        result[
            (
                base_replay_symbol(
                    row[0]
                ),
                as_naive_utc(
                    row[1]
                ),
                as_naive_utc(
                    row[2]
                ),
            )
        ] += 1

    return result


def multiset_match_ratio(
    expected: Counter,
    observed: Counter,
) -> float:
    total = sum(
        expected.values()
    )

    if total == 0:
        return (
            1.0
            if not observed
            else 0.0
        )

    matched = sum(
        (
            expected
            & observed
        ).values()
    )

    return (
        matched
        / total
    )


def previous_bar(
    dates: pd.DatetimeIndex,
    execution_time,
) -> pd.Timestamp:
    target = as_utc(
        execution_time
    )

    location = dates.get_indexer(
        [
            target,
        ]
    )[0]

    if location < 0:
        raise ValueError(
            "execution timestamp not "
            f"present in 1h fabric: {target}"
        )

    if location == 0:
        raise ValueError(
            "execution has no prior "
            f"decision bar: {target}"
        )

    return dates[
        location - 1
    ]


def build_schedule_frame(
    frames: Mapping[
        str,
        pd.DataFrame,
    ],
    trades: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict,
]:
    if trades.empty:
        raise ValueError(
            "cannot build PyBroker "
            "schedule from zero trades"
        )

    laned_trades, lane_audit = (
        assign_replay_lanes(
            trades
        )
    )

    output = []

    entry_signal_count = 0
    exit_signal_count = 0

    for (
        raw_symbol,
        raw_frame,
    ) in frames.items():
        original_symbol = str(
            raw_symbol
        ).upper()

        symbol_trades = (
            laned_trades.loc[
                laned_trades[
                    "symbol"
                ]
                == original_symbol
            ]
        )

        if symbol_trades.empty:
            continue

        for (
            replay_symbol,
            replay_trades,
        ) in symbol_trades.groupby(
            "_replay_symbol",
            sort=True,
        ):
            frame = raw_frame.copy()

            required = {
                "date",
                "open",
                "high",
                "low",
                "close",
            }

            missing = (
                required
                - set(
                    frame.columns
                )
            )

            if missing:
                raise ValueError(
                    f"{original_symbol}: "
                    "missing "
                    f"{sorted(missing)}"
                )

            frame[
                "date"
            ] = pd.to_datetime(
                frame[
                    "date"
                ],
                utc=True,
                errors="coerce",
            )

            frame = (
                frame.dropna(
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

            dates = (
                pd.DatetimeIndex(
                    frame[
                        "date"
                    ]
                )
            )

            frame[
                ENTRY_SIGNAL
            ] = 0

            frame[
                EXIT_SIGNAL
            ] = 0

            date_to_row = {
                timestamp: index
                for index, timestamp
                in enumerate(
                    dates
                )
            }

            for trade in (
                replay_trades
                .itertuples(
                    index=False
                )
            ):
                entry_decision = (
                    previous_bar(
                        dates,
                        trade.entry_time,
                    )
                )

                exit_decision = (
                    previous_bar(
                        dates,
                        trade.exit_time,
                    )
                )

                entry_row = (
                    date_to_row[
                        entry_decision
                    ]
                )

                exit_row = (
                    date_to_row[
                        exit_decision
                    ]
                )

                if (
                    frame.at[
                        entry_row,
                        ENTRY_SIGNAL,
                    ]
                    != 0
                ):
                    raise ValueError(
                        f"{replay_symbol}: "
                        "duplicate scheduled "
                        "entry"
                    )

                if (
                    frame.at[
                        exit_row,
                        EXIT_SIGNAL,
                    ]
                    != 0
                ):
                    raise ValueError(
                        f"{replay_symbol}: "
                        "duplicate scheduled "
                        "exit"
                    )

                frame.at[
                    entry_row,
                    ENTRY_SIGNAL,
                ] = 1

                frame.at[
                    exit_row,
                    EXIT_SIGNAL,
                ] = 1

                entry_signal_count += 1
                exit_signal_count += 1

            collision = (
                (
                    frame[
                        ENTRY_SIGNAL
                    ]
                    == 1
                )
                & (
                    frame[
                        EXIT_SIGNAL
                    ]
                    == 1
                )
            )

            if collision.any():
                timestamps = (
                    frame.loc[
                        collision,
                        "date",
                    ]
                    .astype(str)
                    .tolist()
                )

                raise ValueError(
                    f"{replay_symbol}: "
                    "lane construction "
                    "failed; entry/exit "
                    "collision remains at "
                    f"{timestamps[:5]}"
                )

            frame[
                "symbol"
            ] = str(
                replay_symbol
            )

            if (
                "volume"
                not in frame
            ):
                frame[
                    "volume"
                ] = np.nan

            output.append(
                frame[
                    [
                        "symbol",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        ENTRY_SIGNAL,
                        EXIT_SIGNAL,
                    ]
                ]
            )

    if not output:
        raise ValueError(
            "no replay schedule frames"
        )

    combined = (
        pd.concat(
            output,
            ignore_index=True,
        )
        .sort_values(
            [
                "date",
                "symbol",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    combined[
        "date"
    ] = (
        pd.to_datetime(
            combined[
                "date"
            ],
            utc=True,
        )
        .dt.tz_localize(
            None
        )
    )

    audit = {
        "scheduled_entries": int(
            entry_signal_count
        ),
        "scheduled_exits": int(
            exit_signal_count
        ),
        "expected_trades": int(
            len(
                trades
            )
        ),
        **lane_audit,
    }

    if (
        audit[
            "scheduled_entries"
        ]
        != audit[
            "expected_trades"
        ]
        or audit[
            "scheduled_exits"
        ]
        != audit[
            "expected_trades"
        ]
    ):
        raise ValueError(
            "schedule count mismatch"
        )

    return (
        combined,
        audit,
    )

def fee_callable(
    cost_bps_per_side: float,
):
    bps = Decimal(
        str(
            float(
                cost_bps_per_side
            )
        )
    )

    divisor = Decimal(
        "10000"
    )

    def calculate_fee(
        info,
    ):
        return (
            info.fill_price
            * info.shares
            * bps
            / divisor
        )

    return calculate_fee


def portfolio_metrics(
    portfolio: pd.DataFrame,
    *,
    initial_cash: float,
) -> dict:
    if (
        portfolio is None
        or portfolio.empty
    ):
        return {
            "portfolio_total_return": (
                np.nan
            ),
            "portfolio_max_drawdown": (
                np.nan
            ),
        }

    if (
        "market_value"
        not in portfolio
    ):
        return {
            "portfolio_total_return": (
                np.nan
            ),
            "portfolio_max_drawdown": (
                np.nan
            ),
        }

    equity = pd.to_numeric(
        portfolio[
            "market_value"
        ],
        errors="coerce",
    ).dropna()

    if equity.empty:
        return {
            "portfolio_total_return": (
                np.nan
            ),
            "portfolio_max_drawdown": (
                np.nan
            ),
        }

    total_return = (
        float(
            equity.iloc[
                -1
            ]
            / float(
                initial_cash
            )
            - 1.0
        )
    )

    drawdown = (
        equity
        / equity.cummax()
        - 1.0
    )

    return {
        "portfolio_total_return": (
            total_return
        ),
        "portfolio_max_drawdown": float(
            drawdown.min()
        ),
    }


def run_pybroker_replay(
    frames: Mapping[
        str,
        pd.DataFrame,
    ],
    trades: pd.DataFrame,
    *,
    cost_bps_per_side: float,
    target_weight: float = 0.05,
    initial_cash: float = 1_000_000.0,
) -> dict:
    import pybroker
    from pybroker import (
        PositionMode,
        PriceType,
        Strategy,
        StrategyConfig,
    )

    if (
        target_weight <= 0
        or target_weight >= 1
    ):
        raise ValueError(
            "target_weight must be "
            "between zero and one"
        )

    data, schedule_audit = (
        build_schedule_frame(
            frames,
            trades,
        )
    )

    try:
        pybroker.register_columns(
            ENTRY_SIGNAL,
            EXIT_SIGNAL,
        )
    except Exception as exc:
        message = str(
            exc
        ).lower()

        if (
            "already"
            not in message
            and "registered"
            not in message
        ):
            raise

    symbols = sorted(
        data[
            "symbol"
        ]
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )

    def execute(
        ctx,
    ):
        if ctx.bars < 1:
            return

        position = (
            ctx.long_pos()
        )

        exit_signal = (
            float(
                ctx.scheduled_exit[
                    -1
                ]
            )
            > 0.0
        )

        entry_signal = (
            float(
                ctx.scheduled_entry[
                    -1
                ]
            )
            > 0.0
        )

        if position:
            if exit_signal:
                ctx.sell_shares = (
                    position.shares
                )

                ctx.sell_fill_price = (
                    PriceType.OPEN
                )

            return

        if entry_signal:
            ctx.buy_shares = (
                ctx.calc_target_shares(
                    target_weight
                )
            )

            ctx.buy_fill_price = (
                PriceType.OPEN
            )

    config = StrategyConfig(
        initial_cash=(
            initial_cash
        ),
        fee_mode=(
            fee_callable(
                cost_bps_per_side
            )
        ),
        round_fill_price=False,
        position_mode=(
            PositionMode.LONG_ONLY
        ),
        max_long_positions=(
            len(
                symbols
            )
        ),
        max_short_positions=None,
        buy_delay=1,
        sell_delay=1,
        exit_on_last_bar=False,
        bars_per_year=1764,
        bootstrap_samples=1000,
        bootstrap_sample_size=500,
    )

    start_date = (
        data[
            "date"
        ].min()
    )

    end_date = (
        data[
            "date"
        ].max()
    )

    strategy = Strategy(
        data,
        start_date,
        end_date,
        config,
    )

    strategy.add_execution(
        execute,
        symbols,
    )

    result = (
        strategy.backtest()
    )

    observed = (
        observed_trade_keys(
            result.trades
        )
    )

    expected = (
        expected_trade_keys(
            trades
        )
    )

    if observed is None:
        schedule_match_ratio = (
            float(
                len(
                    result.trades
                )
                == len(
                    trades
                )
            )
        )

        timestamp_parity_available = (
            False
        )

        exact_schedule_match = (
            bool(
                len(
                    result.trades
                )
                == len(
                    trades
                )
            )
        )
    else:
        schedule_match_ratio = (
            multiset_match_ratio(
                expected,
                observed,
            )
        )

        timestamp_parity_available = (
            True
        )

        exact_schedule_match = (
            expected
            == observed
        )

    return {
        "engine": "pybroker",
        "engine_version": str(
            getattr(
                pybroker,
                "__version__",
                "unknown",
            )
        ),
        "validation_mode": (
            "scheduled_trade_"
            "cross_engine_replay"
        ),
        "cost_bps_per_side": (
            float(
                cost_bps_per_side
            )
        ),
        "expected_trade_count": (
            int(
                len(
                    trades
                )
            )
        ),
        "pybroker_trade_count": int(
            len(
                result.trades
            )
        ),
        "pybroker_order_count": int(
            len(
                result.orders
            )
        ),
        "timestamp_parity_available": (
            timestamp_parity_available
        ),
        "schedule_match_ratio": (
            float(
                schedule_match_ratio
            )
        ),
        "exact_schedule_match": (
            bool(
                exact_schedule_match
            )
        ),
        **portfolio_metrics(
            result.portfolio,
            initial_cash=(
                initial_cash
            ),
        ),
        **schedule_audit,
        "execution_authority": (
            "NONE"
        ),
        "broker_calls": 0,
    }


def evaluate_symbol_breadth(
    trades: pd.DataFrame,
    *,
    cost_bps_per_side: float,
) -> dict:
    if trades.empty:
        return {
            "symbol_count": 0,
            "positive_symbol_ratio": 0.0,
            "max_symbol_trade_share": 1.0,
            "symbol_metrics": {},
        }

    metrics = {}

    for (
        symbol,
        group,
    ) in trades.groupby(
        "symbol"
    ):
        metrics[
            str(
                symbol
            )
        ] = trade_metrics(
            group,
            cost_bps_per_side=(
                cost_bps_per_side
            ),
        )

    positive = [
        value[
            "net_expectancy"
        ]
        > 0
        for value
        in metrics.values()
        if value[
            "trades"
        ]
        > 0
    ]

    counts = (
        trades[
            "symbol"
        ]
        .value_counts()
    )

    return {
        "symbol_count": int(
            len(
                metrics
            )
        ),
        "positive_symbol_ratio": (
            float(
                np.mean(
                    positive
                )
            )
            if positive
            else 0.0
        ),
        "max_symbol_trade_share": float(
            counts.max()
            / counts.sum()
        ),
        "symbol_metrics": (
            metrics
        ),
    }


INTRABAR_EXECUTION_STRATEGIES = frozenset(
    {
        "market_structure_atr_pullback",
    }
)


def replay_contract_audit(
    trades: pd.DataFrame,
    *,
    strategy: str,
) -> dict:
    strategy = str(
        strategy
    )

    if trades.empty:
        return {
            "compatible": True,
            "execution_contract": (
                "NEXT_OPEN_REPLAY"
            ),
            "route": (
                "PYBROKER_NEXT_OPEN"
            ),
            "reasons": [],
            "trade_count": 0,
            "nonpositive_duration_trades": 0,
            "same_bar_trades": 0,
        }

    required = {
        "entry_time",
        "exit_time",
    }

    missing = (
        required
        - set(
            trades.columns
        )
    )

    if missing:
        raise ValueError(
            "replay contract input "
            f"missing {sorted(missing)}"
        )

    entry = pd.to_datetime(
        trades[
            "entry_time"
        ],
        utc=True,
        errors="coerce",
    )

    exit_time = pd.to_datetime(
        trades[
            "exit_time"
        ],
        utc=True,
        errors="coerce",
    )

    if (
        entry.isna().any()
        or exit_time.isna().any()
    ):
        raise ValueError(
            "invalid replay-contract "
            "timestamps"
        )

    same_bar = int(
        (
            exit_time
            == entry
        ).sum()
    )

    backwards = int(
        (
            exit_time
            < entry
        ).sum()
    )

    if (
        "duration_bars"
        in trades
    ):
        duration = pd.to_numeric(
            trades[
                "duration_bars"
            ],
            errors="coerce",
        )

        nonpositive_duration = int(
            (
                duration
                <= 0
            ).sum()
        )

    else:
        nonpositive_duration = (
            same_bar
            + backwards
        )

    reasons = []

    if (
        strategy
        in INTRABAR_EXECUTION_STRATEGIES
    ):
        reasons.append(
            "strategy_uses_intrabar_"
            "limit_stop_execution"
        )

    if same_bar:
        reasons.append(
            "same_bar_entry_exit_present"
        )

    if backwards:
        reasons.append(
            "exit_before_entry_present"
        )

    if (
        strategy
        in INTRABAR_EXECUTION_STRATEGIES
    ):
        execution_contract = (
            "1H_SETUP_INTRABAR_EXECUTION"
        )

        route = (
            "1H_SETUP_15M_EXECUTION_VALIDATION"
        )

        compatible = False

    elif (
        same_bar > 0
        or backwards > 0
    ):
        execution_contract = (
            "NON_NEXT_OPEN_EXECUTION"
        )

        route = (
            "EXECUTION_CONTRACT_REVIEW"
        )

        compatible = False

    else:
        execution_contract = (
            "NEXT_OPEN_REPLAY"
        )

        route = (
            "PYBROKER_NEXT_OPEN"
        )

        compatible = True

    return {
        "compatible": bool(
            compatible
        ),
        "execution_contract": (
            execution_contract
        ),
        "route": route,
        "reasons": reasons,
        "trade_count": int(
            len(
                trades
            )
        ),
        "nonpositive_duration_trades": (
            nonpositive_duration
        ),
        "same_bar_trades": (
            same_bar
        ),
        "backwards_trades": (
            backwards
        ),
    }


def classify_crosscheck(
    *,
    usable_folds: int,
    positive_fold_ratio: float,
    stress_positive_fold_ratio: float,
    worst_expectancy_bps: float,
    median_stress_expectancy_bps: float,
    min_schedule_match_ratio: float,
    positive_symbol_ratio: float,
    max_symbol_trade_share: float,
) -> str:
    validated = (
        usable_folds >= 3
        and positive_fold_ratio
        >= 0.75
        and stress_positive_fold_ratio
        >= 0.75
        and worst_expectancy_bps
        > 0
        and median_stress_expectancy_bps
        > 0
        and min_schedule_match_ratio
        >= 0.999999
        and positive_symbol_ratio
        >= 0.50
        and max_symbol_trade_share
        <= 0.60
    )

    provisional = (
        usable_folds >= 2
        and positive_fold_ratio
        >= 0.50
        and stress_positive_fold_ratio
        >= 0.50
        and median_stress_expectancy_bps
        > 0
        and min_schedule_match_ratio
        >= 0.999999
        and max_symbol_trade_share
        <= 0.70
    )

    if validated:
        return (
            "CROSS_ENGINE_VALIDATED"
        )

    if provisional:
        return (
            "CROSS_ENGINE_PROVISIONAL"
        )

    return (
        "CROSS_ENGINE_REJECT"
    )
