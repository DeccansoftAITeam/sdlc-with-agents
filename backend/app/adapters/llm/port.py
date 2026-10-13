"""The one interface to a language model (ADR-0004). Only app.features.ai may use it."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMError(Exception):
    """Provider failure: timeout, HTTP error or an unusable response. Never carries the key."""


class LLM(Protocol):
    async def complete(self, *, model: str, system: str, user: str, max_tokens: int) -> Completion: ...
