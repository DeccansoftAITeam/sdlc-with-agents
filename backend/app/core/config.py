"""Settings come only from the environment (12-factor, AD-02)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DB = "ticketdesk"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TicketDesk"
    environment: str = Field(default="local", description="local | preview | dev | staging | production")
    # Runtime role: no table ownership, NOBYPASSRLS (ADR template: multi-tenancy).
    database_url: str = f"postgresql+asyncpg://{_DB}_app:app@localhost:5432/{_DB}"
    # Owner role: used only by Alembic.
    migration_database_url: str = f"postgresql+asyncpg://{_DB}_owner:owner@localhost:5432/{_DB}"
    otel_exporter_otlp_endpoint: str | None = None
    # Base URL of the web app, used in links sent by email (verify, reset).
    web_base_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
