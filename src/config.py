import datetime as dt
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------- APP CONFIGURATION SETTINGS
class Config(BaseSettings):
    """
    Central configuration for the FastAPI application.

    Loads settings from environment variables and a `.env` file. Includes:
    - Database configuration.
    - CORS configuration for allowing different origins.

    Sensitive values must be stored securely in environment variables and never hardcoded.
    """

    # ----- I. Default
    APP_NAME: str = "FedgeBenefitEmailOrder"
    LATEST_UPDATE: str = dt.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    APP_VERSION: str = "0.1"

    # ----- II. Environmental
    DATABASE_URL: str
    DB_ECHO: bool = True
    ENVIRONMENT: str = "local"
    ALLOW_ORIGINS: str = "*"

    # ----- IV. Meta Configuration
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


# --------------- CONFIGURATION ACCESSORS
@lru_cache
def get_settings() -> Config:
    return Config()

settings = Config()
