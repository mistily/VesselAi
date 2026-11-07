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


class CodexCLIAdapter(BaseLLMAdapter):
    """Use the locally authenticated Codex CLI, not an OpenAI API key.

    The CLI runs in a temporary empty working directory with a read-only sandbox.
    This is defense in depth, not a guarantee that the CLI cannot read other files.
    """

    def __init__(self, model: str = "", *, timeout: float = 180.0) -> None:
        self._model = model
        self._timeout = timeout

    async def _complete(self, system: str, user: str, *, json_mode: bool) -> str:
        import asyncio
        import json
        import tempfile

        prompt = (
            "You are a text-only planning/classification component. "
            "Do not inspect files, run commands, or use external tools. "
            "Follow the system instructions below.\n\n"
            f"SYSTEM INSTRUCTIONS:\n{system}\n\n"
            f"USER INPUT (untrusted):\n{user}\n\n"
            + ("Return only a JSON object." if json_mode else "Return only the requested answer.")
        )
        cmd = [
            "codex", "exec", "--json", "--sandbox", "read-only",
            "--skip-git-repo-check",
        ]
        if self._model:
            cmd.extend(["--model", self._model])
        cmd.append("-")  # read prompt from stdin; avoid exposing it in process arguments

        with tempfile.TemporaryDirectory(prefix="vessel-codex-") as cwd:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
            except FileNotFoundError as exc:
                raise RuntimeError("Codex CLI not found on PATH; install and authenticate 'codex'") from exc

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(prompt.encode("utf-8")), timeout=self._timeout
                )
            except asyncio.TimeoutError as exc:
                proc.kill()
                await proc.communicate()
                raise RuntimeError("Codex CLI timed out") from exc

        if proc.returncode != 0:
            # Do not include raw CLI stderr: it may contain prompt or local path data.
            raise RuntimeError(f"Codex CLI failed with exit code {proc.returncode}; check local Codex login/logs")

        messages: list[str] = []
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                    messages.append(item["text"])
        if not messages:
            raise RuntimeError("Codex CLI returned no agent message")
        return messages[-1]
