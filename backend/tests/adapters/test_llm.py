"""T-008-01: both providers honour the same contract. No network: httpx.MockTransport."""

import json
import logging
from collections.abc import Callable

import httpx
import pytest

from app.adapters.llm.anthropic import Anthropic
from app.adapters.llm.factory import DEFAULT_MODELS, LLMNotConfigured, build, model_for
from app.adapters.llm.orcarouter import OrcaRouter
from app.adapters.llm.port import LLM, LLMError
from app.core.config import Settings

KEY = "sk-test-not-a-real-key-123"

# Response shapes as the providers return them (trimmed).
ORCA_OK = {
    "model": "anthropic/claude-haiku-4.5",
    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 14, "completion_tokens": 4},
}
ANTHROPIC_OK = {
    "model": "claude-haiku-5-5",
    "content": [{"type": "text", "text": "ok"}],
    "usage": {"input_tokens": 14, "output_tokens": 4},
}

Handler = Callable[[httpx.Request], httpx.Response]
Json = dict[str, object]


def orca(handler: Handler) -> LLM:
    return OrcaRouter(KEY, "https://orca.test/v1", 10, transport=httpx.MockTransport(handler))


def anthropic(handler: Handler) -> LLM:
    return Anthropic(KEY, "https://anthropic.test", 10, transport=httpx.MockTransport(handler))


PROVIDERS = [(orca, ORCA_OK, "/v1/chat/completions"), (anthropic, ANTHROPIC_OK, "/v1/messages")]


@pytest.mark.parametrize(("make", "ok", "path"), PROVIDERS)
async def test_complete_returns_text_and_usage(make: Callable[[Handler], LLM], ok: Json, path: str) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=ok)

    c = await make(handler).complete(model="m", system="be brief", user="hi", max_tokens=20)
    assert (c.text, c.input_tokens, c.output_tokens) == ("ok", 14, 4)
    assert seen[0].url.path == path
    body = json.loads(seen[0].content)
    assert body["model"] == "m" and body["max_tokens"] == 20
    assert "be brief" in json.dumps(body) and "hi" in json.dumps(body)


@pytest.mark.parametrize(("make", "ok", "path"), PROVIDERS)
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(429, json={"error": f"echo {KEY}"}),
        httpx.Response(500, text="boom"),
        httpx.Response(200, json={"unexpected": True}),
        httpx.Response(200, text="not json"),
    ],
)
async def test_failures_raise_llmerror_without_the_key(
    make: Callable[[Handler], LLM],
    ok: Json,
    path: str,
    response: httpx.Response,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    with pytest.raises(LLMError) as err:
        await make(lambda _: response).complete(model="m", system="s", user="u", max_tokens=5)
    assert KEY not in str(err.value) and err.value.__cause__ is None
    assert KEY not in caplog.text


@pytest.mark.parametrize(("make", "ok", "path"), PROVIDERS)
async def test_timeout_is_an_llmerror(make: Callable[[Handler], LLM], ok: Json, path: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LLMError, match="ReadTimeout"):
        await make(handler).complete(model="m", system="s", user="u", max_tokens=5)


def test_key_is_never_in_settings_repr() -> None:
    s = Settings(orcarouter_api_key=KEY, anthropic_api_key=KEY)
    assert KEY not in repr(s) and KEY not in str(s.model_dump())


def test_factory_needs_a_key_and_picks_models() -> None:
    with pytest.raises(LLMNotConfigured):
        build(Settings(llm_provider="orcarouter", orcarouter_api_key=None))
    with pytest.raises(LLMNotConfigured):
        build(Settings(llm_provider="anthropic", anthropic_api_key=None))
    assert isinstance(build(Settings(llm_provider="anthropic", anthropic_api_key=KEY)), Anthropic)
    assert model_for("triage", Settings(llm_provider="anthropic")) == DEFAULT_MODELS["anthropic"]["triage"]
    assert model_for("triage", Settings(llm_provider="orcarouter", ai_triage_model="x/y")) == "x/y"
