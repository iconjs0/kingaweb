from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KingaWeb API"
    app_environment: Literal["development", "test", "staging", "production"] = "development"
    app_version: str = "0.1.0"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="KINGAWEB_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
