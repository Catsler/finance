from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PaperTradingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAPER_", extra="ignore")

    db_path: Path = Field(default=Path("results/paper_trading.db"))
    initial_cash: float = Field(default=4_000_000.0, ge=0)

    quote_cache_seconds: int = Field(default=2, ge=0)
    quote_max_age_seconds: int = Field(default=5, ge=0)

    poll_seconds: float = Field(default=2.0, gt=0)

    allow_out_of_session: bool = Field(default=False)

    order_value_limit: float = Field(default=500_000.0, gt=0)
    daily_trades_warn: int = Field(default=10, ge=0)
    daily_trades_reject: int = Field(default=15, ge=0)

    aggressive_timeout_seconds: int = Field(default=5, ge=1)
    limit_timeout_seconds: int = Field(default=180, ge=1)


def get_settings() -> PaperTradingSettings:
    return PaperTradingSettings()
