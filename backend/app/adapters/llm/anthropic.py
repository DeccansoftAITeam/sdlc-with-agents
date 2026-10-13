"""Direct Anthropic Messages API (POST /v1/messages). Plain httpx, no SDK."""

import httpx

from app.adapters.llm.port import Completion, LLMError

API_VERSION = "2023-06-01"


class Anthropic:
    def __init__(
        self, api_key: str, base_url: str, timeout: float, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={"x-api-key": api_key, "anthropic-version": API_VERSION},
            timeout=timeout,
            transport=transport,
        )

    async def complete(self, *, model: str, system: str, user: str, max_tokens: int) -> Completion:
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            r = await self._client.post("v1/messages", json=body)
            r.raise_for_status()
            data = r.json()
            text = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
            usage = data.get("usage") or {}
            return Completion(
                text=text,
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
                model=str(data.get("model", model)),
            )
        except httpx.HTTPStatusError as e:  # status only: the response body may echo the request
            raise LLMError(f"anthropic: HTTP {e.response.status_code}") from None
        except httpx.HTTPError as e:
            raise LLMError(f"anthropic: {type(e).__name__}") from None
        except (KeyError, TypeError, ValueError):
            raise LLMError("anthropic: unexpected response shape") from None
