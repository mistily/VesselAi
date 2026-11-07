from __future__ import annotations

from typing import Protocol

from slack_sdk.web.async_client import AsyncWebClient


class Messenger(Protocol):
    async def post(
        self, channel: str, text: str, *, thread_ts: str | None = None, blocks: list | None = None
    ) -> str: ...

    async def update(self, channel: str, ts: str, text: str, blocks: list | None = None) -> None: ...

    async def ephemeral(
        self, channel: str, user: str, text: str, *, thread_ts: str | None = None
    ) -> None: ...


class SlackMessenger:
    """Thin Slack transport. No behavior lives here."""

    def __init__(self, client: AsyncWebClient) -> None:
        self._c = client

    async def post(self, channel, text, *, thread_ts=None, blocks=None) -> str:
        resp = await self._c.chat_postMessage(
            channel=channel, text=text, thread_ts=thread_ts, blocks=blocks
        )
        return resp["ts"]

    async def update(self, channel, ts, text, blocks=None) -> None:
        await self._c.chat_update(channel=channel, ts=ts, text=text, blocks=blocks)

    async def ephemeral(self, channel, user, text, *, thread_ts=None) -> None:
        await self._c.chat_postEphemeral(channel=channel, user=user, text=text, thread_ts=thread_ts)
