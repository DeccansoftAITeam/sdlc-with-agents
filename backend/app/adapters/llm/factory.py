"""Pick the provider and model ids from settings (ADR-0004)."""

from functools import lru_cache

from app.adapters.llm.anthropic import Anthropic
from app.adapters.llm.fake import FakeLLM
from app.adapters.llm.orcarouter import OrcaRouter
from app.adapters.llm.port import LLM
from app.core.config import Settings, get_settings

# Haiku 5.5 has no capacity on OrcaRouter today (2026-10-13): switch the default when it does.
DEFAULT_MODELS = {
    "orcarouter": {"triage": "anthropic/claude-haiku-4.5", "reply": "anthropic/claude-sonnet-5.5"},
    "anthropic": {"triage": "claude-haiku-5-5", "reply": "claude-sonnet-5-5"},
    "fake": {"triage": "fake-triage", "reply": "fake-reply"},
}


class LLMNotConfigured(Exception):
    pass


def model_for(task: str, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    override = {"triage": s.ai_triage_model, "reply": s.ai_reply_model}[task]
    return override or DEFAULT_MODELS[s.llm_provider][task]


def build(settings: Settings) -> LLM:
    if settings.llm_provider == "fake":
        return FakeLLM()
    if settings.llm_provider == "anthropic":
        if settings.anthropic_api_key is None:
            raise LLMNotConfigured("ANTHROPIC_API_KEY is not set")
        key = settings.anthropic_api_key.get_secret_value()
        return Anthropic(key, settings.anthropic_base_url, settings.llm_timeout_seconds)
    if settings.orcarouter_api_key is None:
        raise LLMNotConfigured("ORCAROUTER_API_KEY is not set")
    key = settings.orcarouter_api_key.get_secret_value()
    return OrcaRouter(key, settings.orcarouter_base_url, settings.llm_timeout_seconds)


@lru_cache
def get_llm() -> LLM:
    return build(get_settings())
