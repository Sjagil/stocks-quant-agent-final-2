from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value in (None, "") else float(value)


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value in (None, "") else int(value)


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class AgentConfig:
    timezone: str = field(default_factory=lambda: _str("TZ", "Europe/Amsterdam"))
    db_url: str = field(default_factory=lambda: _str("DB_URL", "sqlite:///data/live.sqlite3"))
    results_root: str = field(default_factory=lambda: _str("RESULTS_ROOT", "./results"))

    eodhd_api_key: str = field(default_factory=lambda: (
        os.getenv("EODHD_API_KEY")
        or os.getenv("EOD_API_KEY")
        or os.getenv("EODHISTORICALDATA_API_KEY")
        or ""
    ))
    fred_api_key: str = field(default_factory=lambda: _str("FRED_API_KEY", ""))
    openexchange_api_key: str = field(default_factory=lambda: (
        os.getenv("OPENEXCHANGERATES_APP_ID")
        or os.getenv("OPENEXCHANGE_API_KEY")
        or ""
    ))

    ibkr_read_only: bool = field(default_factory=lambda: _bool("IBKR_READ_ONLY", True))
    live_trading_allowed: bool = field(default_factory=lambda: _bool("LIVE_TRADING_ALLOWED", False))
    paper_trading_allowed: bool = field(default_factory=lambda: _bool("PAPER_TRADING_ALLOWED", True))
    manual_override_required: bool = field(default_factory=lambda: _bool("MANUAL_OVERRIDE_REQUIRED", True))
    real_order_execution_enabled: bool = field(default_factory=lambda: _bool("WM_REAL_ORDER_EXECUTION_ENABLED", False))
    understands_live_risk: bool = field(default_factory=lambda: _bool("WM_I_UNDERSTAND_LIVE_RISK", False))

    max_global_open_risk: float = field(default_factory=lambda: _float("MAX_GLOBAL_OPEN_RISK", 0.065))
    max_global_drawdown_soft: float = field(default_factory=lambda: _float("MAX_GLOBAL_DRAWDOWN_SOFT", 0.15))
    max_global_drawdown_hard: float = field(default_factory=lambda: _float("MAX_GLOBAL_DRAWDOWN_HARD", 0.25))
    max_order_notional: float = field(default_factory=lambda: _float("MAX_ORDER_NOTIONAL", 25_000.0))

    max_positions: int = field(default_factory=lambda: _int("WM_ALLOCATOR_MAX_POSITIONS", 8))
    min_position_weight: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MIN_POSITION_WEIGHT", 0.05))
    min_position_notional: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MIN_POSITION_NOTIONAL", 150.0))
    max_single_weight: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MAX_SINGLE_WEIGHT", 0.25))
    max_stock_weight: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MAX_STOCK_WEIGHT", 0.85))
    max_etf_weight: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MAX_ETF_WEIGHT", 0.60))
    max_commodity_weight: float = field(default_factory=lambda: _float("WM_ALLOCATOR_MAX_COMMODITY_WEIGHT", 0.40))
    cash_floor: float = field(default_factory=lambda: _float("WM_ALLOCATOR_CASH_FLOOR", 0.03))
    risk_aversion: float = field(default_factory=lambda: _float("WM_ALLOCATOR_RISK_AVERSION", 4.0))
    turnover_penalty: float = field(default_factory=lambda: _float("WM_ALLOCATOR_TURNOVER_PENALTY", 0.35))

    finbert_model: str = field(default_factory=lambda: _str("WM_FINBERT_MODEL", "ProsusAI/finbert"))
    news_half_life_hours: float = field(default_factory=lambda: _float("WM_NEWS_HALF_LIFE_HOURS", 18.0))
    news_lookback_hours: int = field(default_factory=lambda: _int("WM_NEWS_LOOKBACK_HOURS", 168))

    @property
    def execution_authority(self) -> str:
        return "NONE"

    def assert_safe_agent_mode(self) -> None:
        if self.execution_authority != "NONE":
            raise RuntimeError("Intelligence agent execution authority must remain NONE")
