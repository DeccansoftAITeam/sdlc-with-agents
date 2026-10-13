"""OrcaRouter: an OpenAI-compatible gateway (POST /chat/completions). Plain httpx, no SDK."""

import httpx

from app.adapters.llm.port import Completion, LLMError


class OrcaRouter:
    def __init__(
        self, api_key: str, base_url: str, timeout: float, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            transport=transport,
        )

    async def complete(self, *, model: str, system: str, user: str, max_tokens: int) -> Completion:
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            r = await self._client.post("chat/completions", json=body)
            r.raise_for_status()
            data = r.json()
            usage = data.get("usage") or {}
            return Completion(
                text=data["choices"][0]["message"]["content"] or "",
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
                model=str(data.get("model", model)),
            )
        except httpx.HTTPStatusError as e:  # status only: the response body may echo the request
            raise LLMError(f"orcarouter: HTTP {e.response.status_code}") from None
        except httpx.HTTPError as e:
            raise LLMError(f"orcarouter: {type(e).__name__}") from None
        except (KeyError, IndexError, TypeError, ValueError):
            raise LLMError("orcarouter: unexpected response shape") from None
