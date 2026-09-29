"""Application configuration for the KARNA backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env files."""

    app_name: str = "KARNA"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./karna.db"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="KARNA_",
        extra="ignore",
    )


settings = Settings()
