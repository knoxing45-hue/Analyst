"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    app_name: str = "Market Analysis Agent"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./market_agent.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Market data
    yfinance_enabled: bool = True
    alpha_vantage_enabled: bool = False
    alpha_vantage_api_key: str = ""
    tradingview_enabled: bool = True

    # Defaults
    default_risk_percent: float = 1.0
    default_sizing_pref: str = "lots"
    default_account_size: float = 10000.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
