"""HTTP-only provider adapters (no vendor SDKs). Add a provider = add a class here."""
from __future__ import annotations

import httpx

from .base import BaseLLMAdapter


class AnthropicAdapter(BaseLLMAdapter):
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(
        self, api_key: str, model: str, *, max_tokens: int = 4096,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._key, self._model, self._max_tokens = api_key, model, max_tokens
        self._client = client or httpx.AsyncClient(timeout=60)

    async def _complete(self, system: str, user: str, *, json_mode: bool) -> str:
        resp = await self._client.post(
            self.URL,
            headers={
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": self._max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        resp.raise_for_status()
        return "".join(b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text")

    async def aclose(self) -> None:
        await self._client.aclose()


class OpenAICompatAdapter(BaseLLMAdapter):
    """OpenAI, or any server speaking /chat/completions (Ollama, vLLM, LM Studio...)."""

    def __init__(
        self, api_key: str, model: str, *, base_url: str = "https://api.openai.com/v1",
        json_mode: bool = True, client: httpx.AsyncClient | None = None,
    ) -> None:
        self._key, self._model = api_key, model
        self._base = base_url.rstrip("/")
        self._json_mode = json_mode
        self._client = client or httpx.AsyncClient(timeout=120)

    async def _complete(self, system: str, user: str, *, json_mode: bool) -> str:
        body: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode and self._json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = await self._client.post(
            f"{self._base}/chat/completions",
            headers={"Authorization": f"Bearer {self._key}"},
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""

    async def aclose(self) -> None:
        await self._client.aclose()
