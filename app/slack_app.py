"""Slack Bolt wiring: parse the Slack payload, hand off to handler.py, return fast."""
from __future__ import annotations

from slack_bolt.async_app import AsyncApp

from .handler import Deps, IncomingEvent, handle_decision, handle_event, spawn
from .slack_ui import ACTION_APPROVE, ACTION_REJECT


def register_handlers(app: AsyncApp, deps: Deps) -> None:
    # Socket Mode: Slack authenticates over the websocket, so there is no URL-verification
    # challenge and no public endpoint. Bolt acks events immediately; the LLM call runs in a
    # background task so we are never near the 3 s limit.

    @app.event("app_mention")
    async def on_mention(event, body):
        spawn(handle_event(IncomingEvent(
            event_id=body["event_id"],
            channel_id=event["channel"],
            user_id=event["user"],
            text=event.get("text", ""),
            thread_ts=event.get("thread_ts") or event["ts"],
            source="mention",
        ), deps))

    @app.event("message")
    async def on_message(event, body):
        # Only human DMs. Ignore bot messages, edits, deletions, joins, etc.
        if event.get("channel_type") != "im" or event.get("subtype") or event.get("bot_id"):
            return
        spawn(handle_event(IncomingEvent(
            event_id=body["event_id"],
            channel_id=event["channel"],
            user_id=event["user"],
            text=event.get("text", ""),
            thread_ts=event.get("thread_ts") or event["ts"],
            source="dm",
        ), deps))

    @app.command("/plan")
    async def on_command(ack, command):
        await ack("On it — I'll reply in a thread.")
        spawn(handle_event(IncomingEvent(
            event_id=f"cmd:{command['trigger_id']}",
            channel_id=command["channel_id"],
            user_id=command["user_id"],
            text=command.get("text", ""),
            thread_ts=None,
            source="command",
        ), deps))

    def _decision_handler(decision: str):
        async def _handler(ack, body, action):
            await ack()
            spawn(handle_decision(
                plan_id=action["value"],
                decision=decision,  # type: ignore[arg-type]
                user_id=body["user"]["id"],
                channel_id=body["channel"]["id"],
                message_ts=body["container"]["message_ts"],
                d=deps,
            ))
        return _handler

    app.action(ACTION_APPROVE)(_decision_handler("approve"))
    app.action(ACTION_REJECT)(_decision_handler("reject"))
