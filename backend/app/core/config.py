"""Settings come only from the environment (12-factor, AD-02)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
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
    # Ed25519 private key (PEM) for signing access tokens (ADR-0002). From Key Vault in
    # deployed environments; when unset and environment=local, an ephemeral key is generated.
    jwt_private_key_pem: str | None = None
    # Explicit opt-in for an in-memory key (local dev and tests ONLY). Never set in deployments.
    jwt_ephemeral_key: bool = False
    # Browser-facing path prefix: Next.js proxies /api/* to this API (refresh-cookie path).
    cookie_path_prefix: str = "/api"

    # AI (ADR-0004). Global kill-switch: off unless explicitly enabled.
    ai_enabled: bool = False
    llm_provider: Literal["orcarouter", "anthropic", "fake"] = "orcarouter"
    # SecretStr: never printed by repr(), logs or tracebacks.
    orcarouter_api_key: SecretStr | None = None
    orcarouter_base_url: str = "https://api.orcarouter.ai/v1"
    anthropic_api_key: SecretStr | None = None
    anthropic_base_url: str = "https://api.anthropic.com"
    # Model ids are settings, not code. None = the provider's default (adapters/llm/factory.py).
    ai_triage_model: str | None = None
    ai_reply_model: str | None = None
    llm_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
