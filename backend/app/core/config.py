from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "eBay Monitor MVP"
    app_env: str = "development"
    api_prefix: str = "/api"
    debug: bool = True
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ebay_monitor"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    timezone: str = "UTC"

    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_marketplace_id: str = "EBAY_US"
    ebay_api_base_url: str = "https://api.ebay.com"
    ebay_auth_base_url: str = "https://api.ebay.com"
    ebay_oauth_scope: str = "https://api.ebay.com/oauth/api_scope"
    ebay_request_timeout_seconds: float = 10.0
    ebay_max_retries: int = 3
    scheduler_daily_hour_utc: int = 9
    scheduler_daily_minute_utc: int = 0
    enable_scheduler: bool = True
    cron_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
