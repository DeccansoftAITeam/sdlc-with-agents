"""Deterministic stand-in for tests and local runs without a key. Records every call."""

from dataclasses import dataclass, field

from app.adapters.llm.port import Completion, LLMError


@dataclass
class FakeLLM:
    reply: str = '{"category": "other", "priority": "P3", "reason": "Fake model"}'
    input_tokens: int = 100
    output_tokens: int = 20
    fail_times: int = 0  # raise LLMError this many times before answering
    calls: list[dict[str, object]] = field(default_factory=list)

    async def complete(self, *, model: str, system: str, user: str, max_tokens: int) -> Completion:
        self.calls.append({"model": model, "system": system, "user": user, "max_tokens": max_tokens})
        if self.fail_times > 0:
            self.fail_times -= 1
            raise LLMError("fake: simulated failure")
        return Completion(self.reply, self.input_tokens, self.output_tokens, model)
