from __future__ import annotations

import argparse
import datetime as dt
import logging
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pandas_ta_classic as ta
import yfinance as yf
from scipy.stats import norm


# ============================================================
# CONFIG
# ============================================================

pd.set_option("display.max_columns", None)

LOGGER = logging.getLogger("market_setup")

UTC = dt.timezone.utc
NY_TZ = ZoneInfo("America/New_York")

REQUIRED_OHLCV = {"open", "high", "low", "close", "volume"}


@dataclass(frozen=True)
class StrategyConfig:
    symbol: str = "SPY"

    # Historische data
    lookback_days: int = 730

    # Indicators
    rsi_length: int = 2
    adx_length: int = 5
    bb_length: int = 20
    bb_std: float = 2.0
    sma_length: int = 200
    atr_length: int = 14

    # Setup thresholds
    rsi_entry_max: float = 10.0
    adx_entry_max: float = 35.0

    # Risk
    atr_stop_multiple: float = 1.5

    # GEX
    risk_free_rate: float = 0.045
    dividend_yield: float = 0.0
    gex_max_dte: int = 45
    gex_max_expiries: int = 6

    # Alleen strikes binnen deze band meenemen
    gex_moneyness_min: float = 0.70
    gex_moneyness_max: float = 1.30

    # Orderflow
    imbalance_ratio: float = 3.0
    min_stacked_imbalances: int = 3


@dataclass(frozen=True)
class GEXResult:
    spot: float
    net_gex_1pct: float
    gross_gex_1pct: float
    call_wall: float | None
    put_wall: float | None
    expiries_used: tuple[str, ...]
    option_rows_used: int

    @property
    def regime(self) -> str:
        if self.net_gex_1pct > 0:
            return "POSITIVE_GEX_PROXY"

        if self.net_gex_1pct < 0:
            return "NEGATIVE_GEX_PROXY"

        return "NEUTRAL_GEX_PROXY"


@dataclass(frozen=True)
class OrderflowResult:
    trigger: str
    max_buy_stack: int
    max_sell_stack: int


# ============================================================
# DATA
# ============================================================

def get_data(
    symbol: str,
    start: dt.date | str,
    end: dt.date | str,
) -> pd.DataFrame:
    """
    Haalt dagelijkse OHLCV-data op.

    end is bewust exclusief.
    Als end=today wordt gebruikt, analyseren we dus geen
    potentieel nog open daily candle.
    """

    LOGGER.info(
        "Historische data ophalen | symbol=%s | start=%s | end=%s",
        symbol,
        start,
        end,
    )

    df = yf.Ticker(symbol).history(
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        actions=False,
        repair=True,
        raise_errors=True,
    )

    if df.empty:
        raise ValueError(
            f"Geen historische data gevonden voor {symbol}."
        )

    df = df.reset_index()
    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    # Sommige feeds gebruiken date, andere datetime
    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    missing = REQUIRED_OHLCV.difference(df.columns)

    if missing:
        raise ValueError(
            f"Ontbrekende OHLCV-kolommen: {sorted(missing)}"
        )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    df[numeric_columns] = df[numeric_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    df = (
        df
        .drop_duplicates(subset=["date"], keep="last")
        .sort_values("date")
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index(drop=True)
    )

    if len(df) < 220:
        raise ValueError(
            f"Slechts {len(df)} candles beschikbaar. "
            "Te weinig voor SMA200 + warm-up."
        )

    return df


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def find_indicator_column(
    df: pd.DataFrame,
    prefix: str,
) -> str:

    matches = [
        column
        for column in df.columns
        if str(column).upper().startswith(prefix.upper())
    ]

    if not matches:
        raise KeyError(
            f"Geen indicator-kolom gevonden voor prefix {prefix}"
        )

    return matches[0]


def calculate_technical_setup(
    df: pd.DataFrame,
    config: StrategyConfig,
) -> pd.DataFrame:

    df = df.copy()

    # RSI
    df["rsi_2"] = ta.rsi(
        df["close"],
        length=config.rsi_length,
    )

    # ADX
    adx = ta.adx(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        length=config.adx_length,
    )

    if adx is None or adx.empty:
        raise ValueError("ADX-berekening mislukt.")

    adx_column = find_indicator_column(
        adx,
        f"ADX_{config.adx_length}",
    )

    df["adx_5"] = adx[adx_column]

    # Bollinger Bands
    bb = ta.bbands(
        close=df["close"],
        length=config.bb_length,
        std=config.bb_std,
    )

    if bb is None or bb.empty:
        raise ValueError("Bollinger Bands-berekening mislukt.")

    lower_col = find_indicator_column(
        bb,
        f"BBL_{config.bb_length}",
    )

    middle_col = find_indicator_column(
        bb,
        f"BBM_{config.bb_length}",
    )

    upper_col = find_indicator_column(
        bb,
        f"BBU_{config.bb_length}",
    )

    df["bb_lower"] = bb[lower_col]
    df["bb_middle"] = bb[middle_col]
    df["bb_upper"] = bb[upper_col]

    # SMA
    df["sma_200"] = ta.sma(
        df["close"],
        length=config.sma_length,
    )

    # ATR
    df["atr_14"] = ta.atr(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        length=config.atr_length,
    )

    # Extra features voor research
    df["atr_pct"] = (
        df["atr_14"] /
        df["close"] *
        100
    )

    df["distance_sma200_pct"] = (
        df["close"] /
        df["sma_200"] -
        1
    ) * 100

    bb_width = (
        df["bb_upper"] -
        df["bb_lower"]
    )

    df["bb_position"] = (
        (df["close"] - df["bb_lower"]) /
        bb_width.replace(0, np.nan)
    )

    return df


# ============================================================
# BLACK-SCHOLES GAMMA
# ============================================================

def black_scholes_gamma(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    sigma: float,
    dividend_yield: float = 0.0,
) -> float:

    if (
        spot <= 0
        or strike <= 0
        or time_to_expiry <= 0
        or sigma <= 0
    ):
        return 0.0

    values = [
        spot,
        strike,
        time_to_expiry,
        rate,
        sigma,
        dividend_yield,
    ]

    if not np.isfinite(values).all():
        return 0.0

    sqrt_t = np.sqrt(time_to_expiry)

    d1 = (
        np.log(spot / strike)
        +
        (
            rate
            - dividend_yield
            + 0.5 * sigma**2
        ) * time_to_expiry
    ) / (
        sigma * sqrt_t
    )

    gamma = (
        np.exp(
            -dividend_yield * time_to_expiry
        )
        *
        norm.pdf(d1)
        /
        (
            spot *
            sigma *
            sqrt_t
        )
    )

    return float(gamma)


# ============================================================
# GEX
# ============================================================

def expiry_close_utc(
    expiry: str,
) -> dt.datetime:

    expiry_date = dt.date.fromisoformat(expiry)

    # Amerikaanse equity options grofweg modelleren
    # tot 16:00 New York tijd.
    close_ny = dt.datetime.combine(
        expiry_date,
        dt.time(16, 0),
        tzinfo=NY_TZ,
    )

    return close_ny.astimezone(UTC)


def process_option_side(
    option_df: pd.DataFrame,
    *,
    side: str,
    spot: float,
    expiry: str,
    now_utc: dt.datetime,
    config: StrategyConfig,
) -> pd.DataFrame:

    if option_df is None or option_df.empty:
        return pd.DataFrame()

    required = {
        "strike",
        "openInterest",
        "impliedVolatility",
    }

    if not required.issubset(option_df.columns):
        return pd.DataFrame()

    df = option_df.copy()

    for column in [
        "strike",
        "openInterest",
        "impliedVolatility",
        "volume",
        "bid",
        "ask",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df = df.dropna(
        subset=[
            "strike",
            "openInterest",
            "impliedVolatility",
        ]
    )

    # Slechte / nutteloze contract rows verwijderen
    df = df[
        (df["strike"] > 0)
        &
        (df["openInterest"] > 0)
        &
        (df["impliedVolatility"] > 0.01)
        &
        (df["impliedVolatility"] < 5.0)
    ]

    # Extreme strikes niet laten domineren
    minimum_strike = (
        spot *
        config.gex_moneyness_min
    )

    maximum_strike = (
        spot *
        config.gex_moneyness_max
    )

    df = df[
        df["strike"].between(
            minimum_strike,
            maximum_strike,
        )
    ]

    if df.empty:
        return df

    expiration = expiry_close_utc(expiry)

    seconds_left = (
        expiration -
        now_utc
    ).total_seconds()

    if seconds_left <= 0:
        return pd.DataFrame()

    # Voorkomt enorme gamma door T -> 0
    minimum_seconds = 30 * 60

    seconds_left = max(
        seconds_left,
        minimum_seconds,
    )

    T = (
        seconds_left /
        (
            365.0 *
            24 *
            60 *
            60
        )
    )

    gammas = []

    for strike, iv in zip(
        df["strike"],
        df["impliedVolatility"],
    ):
        gamma = black_scholes_gamma(
            spot=spot,
            strike=float(strike),
            time_to_expiry=T,
            rate=config.risk_free_rate,
            sigma=float(iv),
            dividend_yield=config.dividend_yield,
        )

        gammas.append(gamma)

    df["gamma"] = gammas

    # Gamma exposure proxy per 1% move
    unsigned_gex = (
        df["openInterest"].astype(float)
        *
        df["gamma"]
        *
        spot**2
        *
        100
        *
        0.01
    )

    # BELANGRIJK:
    # calls positief / puts negatief is slechts een proxy.
    # Wij observeren dealer inventory niet rechtstreeks.
    if side == "call":
        df["gex_1pct"] = unsigned_gex

    elif side == "put":
        df["gex_1pct"] = -unsigned_gex

    else:
        raise ValueError(
            f"Ongeldige option side: {side}"
        )

    df["side"] = side
    df["expiry"] = expiry

    return df


def calculate_gex(
    symbol: str,
    config: StrategyConfig,
) -> GEXResult:

    ticker = yf.Ticker(symbol)

    # Raw spotprijs gebruiken voor options
    history = ticker.history(
        period="5d",
        interval="1d",
        auto_adjust=False,
        actions=False,
        repair=True,
        raise_errors=True,
    )

    if history.empty:
        raise ValueError(
            f"Geen actuele spotdata voor {symbol}."
        )

    closes = pd.to_numeric(
        history["Close"],
        errors="coerce",
    ).dropna()

    if closes.empty:
        raise ValueError(
            "Geen geldige Close gevonden."
        )

    spot = float(closes.iloc[-1])

    expiries = list(
        ticker.options or []
    )

    if not expiries:
        return GEXResult(
            spot=spot,
            net_gex_1pct=0.0,
            gross_gex_1pct=0.0,
            call_wall=None,
            put_wall=None,
            expiries_used=tuple(),
            option_rows_used=0,
        )

    now_utc = dt.datetime.now(
        tz=UTC
    )

    selected_expiries = []

    for expiry in expiries:

        try:
            expiry_date = dt.date.fromisoformat(
                expiry
            )
        except ValueError:
            continue

        dte = (
            expiry_date -
            now_utc.date()
        ).days

        if (
            0 <= dte <= config.gex_max_dte
        ):
            selected_expiries.append(
                expiry
            )

        if (
            len(selected_expiries)
            >= config.gex_max_expiries
        ):
            break

    option_frames = []

    for expiry in selected_expiries:

        try:
            chain = ticker.option_chain(
                expiry
            )

        except Exception as exc:
            LOGGER.warning(
                "Option chain mislukt | %s | %s | %s",
                symbol,
                expiry,
                exc,
            )
            continue

        calls = process_option_side(
            chain.calls,
            side="call",
            spot=spot,
            expiry=expiry,
            now_utc=now_utc,
            config=config,
        )

        puts = process_option_side(
            chain.puts,
            side="put",
            spot=spot,
            expiry=expiry,
            now_utc=now_utc,
            config=config,
        )

        if not calls.empty:
            option_frames.append(calls)

        if not puts.empty:
            option_frames.append(puts)

    if not option_frames:
        return GEXResult(
            spot=spot,
            net_gex_1pct=0.0,
            gross_gex_1pct=0.0,
            call_wall=None,
            put_wall=None,
            expiries_used=tuple(selected_expiries),
            option_rows_used=0,
        )

    all_options = pd.concat(
        option_frames,
        ignore_index=True,
    )

    profile = (
        all_options
        .pivot_table(
            index="strike",
            columns="side",
            values="gex_1pct",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    if "call" not in profile:
        profile["call"] = 0.0

    if "put" not in profile:
        profile["put"] = 0.0

    profile["net"] = (
        profile["call"] +
        profile["put"]
    )

    profile["gross"] = (
        profile["call"].abs() +
        profile["put"].abs()
    )

    call_wall = None
    put_wall = None

    if (profile["call"] > 0).any():
        call_wall = float(
            profile.loc[
                profile["call"].idxmax(),
                "strike",
            ]
        )

    if (profile["put"] < 0).any():
        put_wall = float(
            profile.loc[
                profile["put"].idxmin(),
                "strike",
            ]
        )

    return GEXResult(
        spot=spot,
        net_gex_1pct=float(
            profile["net"].sum()
        ),
        gross_gex_1pct=float(
            profile["gross"].sum()
        ),
        call_wall=call_wall,
        put_wall=put_wall,
        expiries_used=tuple(
            selected_expiries
        ),
        option_rows_used=len(
            all_options
        ),
    )


# ============================================================
# ORDERFLOW
# ============================================================

def check_orderflow_trigger(
    footprint: dict[
        float,
        dict[str, float]
    ],
    *,
    min_ratio: float = 3.0,
    min_stacked_levels: int = 3,
) -> OrderflowResult:
    """
    Detecteert daadwerkelijk opeenvolgende diagonale imbalances.

    Buy:
        ask op hoger prijsniveau /
        bid op prijsniveau eronder

    Sell:
        bid op lager prijsniveau /
        ask op prijsniveau erboven
    """

    if min_ratio <= 1:
        raise ValueError(
            "min_ratio moet groter dan 1 zijn."
        )

    prices = sorted(
        float(price)
        for price in footprint
    )

    if len(prices) < 2:
        return OrderflowResult(
            "NO_TRIGGER",
            0,
            0,
        )

    buy_run = 0
    sell_run = 0

    max_buy_run = 0
    max_sell_run = 0

    for lower_price, upper_price in zip(
        prices[:-1],
        prices[1:],
    ):

        lower = footprint[lower_price]
        upper = footprint[upper_price]

        lower_bid = max(
            float(
                lower.get(
                    "bid_vol",
                    0,
                )
            ),
            0,
        )

        upper_ask = max(
            float(
                upper.get(
                    "ask_vol",
                    0,
                )
            ),
            0,
        )

        buy_imbalance = (
            lower_bid > 0
            and
            upper_ask / lower_bid
            >= min_ratio
        )

        sell_imbalance = (
            upper_ask > 0
            and
            lower_bid / upper_ask
            >= min_ratio
        )

        if buy_imbalance:
            buy_run += 1
        else:
            buy_run = 0

        if sell_imbalance:
            sell_run += 1
        else:
            sell_run = 0

        max_buy_run = max(
            max_buy_run,
            buy_run,
        )

        max_sell_run = max(
            max_sell_run,
            sell_run,
        )

    if (
        max_buy_run >= min_stacked_levels
        and
        max_buy_run > max_sell_run
    ):
        trigger = "BUY_TRIGGER"

    elif (
        max_sell_run >= min_stacked_levels
        and
        max_sell_run > max_buy_run
    ):
        trigger = "SELL_TRIGGER"

    else:
        trigger = "NO_TRIGGER"

    return OrderflowResult(
        trigger=trigger,
        max_buy_stack=max_buy_run,
        max_sell_stack=max_sell_run,
    )


# ============================================================
# DEMO DATA
# ============================================================

def simulated_footprint():
    """
    ALLEEN VOOR TESTS.

    Dit mag nooit als live orderflow worden behandeld.
    """

    return {
        3950.00: {
            "bid_vol": 10,
            "ask_vol": 5,
        },
        3951.00: {
            "bid_vol": 10,
            "ask_vol": 40,
        },
        3952.00: {
            "bid_vol": 10,
            "ask_vol": 40,
        },
        3953.00: {
            "bid_vol": 10,
            "ask_vol": 40,
        },
    }


# ============================================================
# SETUP LOGIC
# ============================================================

def evaluate_setup(
    row: pd.Series,
    gex: GEXResult,
    config: StrategyConfig,
):

    checks = {
        "positive_gex_proxy":
            gex.net_gex_1pct > 0,

        "above_sma200":
            row["close"] > row["sma_200"],

        "rsi2_oversold":
            row["rsi_2"] < config.rsi_entry_max,

        "below_lower_bb":
            row["close"] <= row["bb_lower"],

        "adx_not_extreme":
            row["adx_5"] <= config.adx_entry_max,
    }

    setup_ready = all(
        checks.values()
    )

    return setup_ready, checks


# ============================================================
# RESEARCH RUNNER
# ============================================================

def run_research(
    config: StrategyConfig,
    demo_footprint: bool = False,
):

    today = dt.datetime.now().date()

    start = (
        today -
        dt.timedelta(
            days=config.lookback_days
        )
    )

    print(
        f"\n{'=' * 60}"
        f"\n{config.symbol} RESEARCH SETUP"
        f"\n{'=' * 60}"
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    print("\n[1] GEX CONTEXT")

    gex = calculate_gex(
        config.symbol,
        config,
    )

    print(
        f"Spot:                 {gex.spot:,.2f}"
    )
    print(
        f"Net GEX / 1% proxy:   {gex.net_gex_1pct:,.0f}"
    )
    print(
        f"Gross GEX / 1%:       {gex.gross_gex_1pct:,.0f}"
    )
    print(
        f"Regime:               {gex.regime}"
    )
    print(
        f"Put wall:             {gex.put_wall}"
    )
    print(
        f"Call wall:            {gex.call_wall}"
    )
    print(
        f"Expiries gebruikt:    "
        f"{', '.join(gex.expiries_used) or 'geen'}"
    )
    print(
        f"Option rows gebruikt: {gex.option_rows_used}"
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    print("\n[2] TECHNICAL SETUP")

    df = get_data(
        config.symbol,
        start,
        today,
    )

    df = calculate_technical_setup(
        df,
        config,
    )

    required = [
        "rsi_2",
        "adx_5",
        "bb_lower",
        "bb_upper",
        "sma_200",
        "atr_14",
    ]

    ready_df = df.dropna(
        subset=required
    )

    if ready_df.empty:
        raise ValueError(
            "Geen volledig opgewarmde candle beschikbaar."
        )

    last = ready_df.iloc[-1]

    print(
        f"Date:      {last['date']}"
    )
    print(
        f"Close:     {last['close']:.2f}"
    )
    print(
        f"SMA200:    {last['sma_200']:.2f}"
    )
    print(
        f"RSI(2):    {last['rsi_2']:.2f}"
    )
    print(
        f"ADX(5):    {last['adx_5']:.2f}"
    )
    print(
        f"BB Lower:  {last['bb_lower']:.2f}"
    )
    print(
        f"ATR(14):   {last['atr_14']:.2f}"
    )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    print("\n[3] SETUP GATES")

    setup_ready, checks = evaluate_setup(
        last,
        gex,
        config,
    )

    for name, passed in checks.items():

        status = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"{status:4} | {name}"
        )

    if not setup_ready:

        print(
            "\nGEEN SETUP."
            "\nGeen orderflow-analyse nodig."
        )

        return

    print(
        "\nSETUP READY."
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    print("\n[4] ORDERFLOW")

    if not demo_footprint:

        print(
            "Geen echte footprint-feed aangesloten."
        )

        print(
            "Orderflow confirmation = BLOCKED"
        )

        return

    footprint = simulated_footprint()

    result = check_orderflow_trigger(
        footprint,
        min_ratio=config.imbalance_ratio,
        min_stacked_levels=(
            config.min_stacked_imbalances
        ),
    )

    print(
        f"Trigger:         {result.trigger}"
    )
    print(
        f"Buy stack:       {result.max_buy_stack}"
    )
    print(
        f"Sell stack:      {result.max_sell_stack}"
    )

    # --------------------------------------------------------
    # RESEARCH CANDIDATE
    # --------------------------------------------------------

    if result.trigger == "BUY_TRIGGER":

        entry = float(
            last["close"]
        )

        atr = float(
            last["atr_14"]
        )

        stop = (
            entry -
            config.atr_stop_multiple *
            atr
        )

        risk_per_share = (
            entry -
            stop
        )

        print(
            "\nRESEARCH BUY CANDIDATE"
        )
        print(
            f"Entry reference: {entry:.2f}"
        )
        print(
            f"ATR stop:        {stop:.2f}"
        )
        print(
            f"Risk/share:      {risk_per_share:.2f}"
        )

        print(
            "\nNO ORDER SENT."
        )
        print(
            "Dit script heeft bewust geen execution authority."
        )


# ============================================================
# CLI
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Technical + GEX + "
            "orderflow research setup"
        )
    )

    parser.add_argument(
        "--symbol",
        default="SPY",
    )

    parser.add_argument(
        "--demo-footprint",
        action="store_true",
        help=(
            "Gebruik simulated footprint "
            "uitsluitend voor het testen van de logica."
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
    )

    args = parse_args()

    config = StrategyConfig(
        symbol=args.symbol.upper().strip()
    )

    try:

        run_research(
            config,
            demo_footprint=args.demo_footprint,
        )

    except Exception:

        LOGGER.exception(
            "Research-run mislukt."
        )

        raise


if __name__ == "__main__":
    main()