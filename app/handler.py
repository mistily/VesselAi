"""All behavior lives here as plain async functions. Slack is only the transport."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Coroutine, Literal

from agents.base import AgentContext, BaseAgent
from agents.registry import role_request

from .executor import Executor
from .messenger import Messenger
from .pm_agent import PMAgent
from .repository import PlanRepository
from .router import VesselRouter, clean_text
from .schemas import Plan
from .slack_ui import clip, plan_card, result_message

log = logging.getLogger(__name__)

HELP_TEXT = (
    "Hi! I turn project ideas into structured plans. Mention me (or use `/plan`) with something "
    "like _plan the Q3 checkout migration_. I'll draft a plan, and an approver must sign off "
    "before anything is executed. For focused help, use `/ask developer <question>` or prefix "
    "a message with `developer:`, `requirements:`, `knowledge:`, `qa:`, or `operations:`."
)
OUT_OF_SCOPE_TEXT = "That's outside what I can help with. I only do project planning or explicit agent requests."
PLAN_FAILED_TEXT = "⚠️ I couldn't produce a valid plan for that. Nothing was executed — try rephrasing."
AGENT_FAILED_TEXT = "⚠️ I couldn't complete that agent request. Nothing was changed — please try again."
AGENT_REQUEST_HELP = (
    "Choose an agent and include a request, for example `/ask developer explain this implementation` "
    "or `/ask requirements: define acceptance criteria`."
)


@dataclass(frozen=True)
class IncomingEvent:
    event_id: str
    channel_id: str
    user_id: str
    text: str
    thread_ts: str | None
    source: Literal["mention", "dm", "command", "ask"]


@dataclass
class Deps:
    repo: PlanRepository
    messenger: Messenger
    router: VesselRouter
    agents: dict[str, PMAgent]
    executor: Executor
    approver_ids: frozenset[str]
    require_separate_approver: bool = False
    role_agents: dict[str, BaseAgent] = field(default_factory=dict)


_tasks: set[asyncio.Task] = set()


def spawn(coro: Coroutine) -> asyncio.Task:
    """Fire-and-forget that keeps a strong reference and logs failures."""
    task = asyncio.create_task(coro)
    _tasks.add(task)

    def _done(t: asyncio.Task) -> None:
        _tasks.discard(t)
        if not t.cancelled() and t.exception():
            log.error("background task crashed", exc_info=t.exception())

    task.add_done_callback(_done)
    return task


async def handle_event(ev: IncomingEvent, d: Deps) -> None:
    text = clean_text(ev.text)
    plan_id = d.repo.claim_event(ev.event_id, ev.channel_id, ev.thread_ts, ev.user_id, text)
    if plan_id is None:
        log.info("duplicate event %s ignored", ev.event_id)
        return
    d.repo.audit(
        plan_id, "event_received", ev.user_id, f"source={ev.source}",
        {"event_id": ev.event_id, "channel": ev.channel_id, "user": ev.user_id, "text": text},
    )

    placeholder_ts: str | None = None
    thread_ts = ev.thread_ts
    try:
        if thread_ts is None:
            thread_ts = await d.messenger.post(
                ev.channel_id, f"<@{ev.user_id}> requested a plan: {clip(text, 300)}"
            )
            d.repo.set_thread(plan_id, thread_ts)

        agent_request = role_request(text, d.role_agents)
        if ev.source == "ask" and agent_request is None:
            d.repo.transition(plan_id, "pending", "ignored")
            await d.messenger.post(ev.channel_id, AGENT_REQUEST_HELP, thread_ts=thread_ts)
            return
        if agent_request is not None:
            agent, request = agent_request
            d.repo.set_intent(plan_id, f"agent:{agent.name}")
            placeholder_ts = await d.messenger.post(
                ev.channel_id, f"⏳ {agent.name} is working…", thread_ts=thread_ts
            )
            result = await agent.arun(
                request,
                AgentContext(channel=ev.channel_id, requester=ev.user_id),
            )
            d.repo.transition(plan_id, "pending", "ignored")
            response = f"*{result.agent}*\n{result.response}"
            await d.messenger.update(ev.channel_id, placeholder_ts, clip(response, 3500))
            return

        decision = await d.router.route(text, ev.source)
        d.repo.set_intent(plan_id, decision.intent)
        d.repo.audit(plan_id, "event_received", "system",
                     f"routed intent={decision.intent} via={decision.via}: {decision.reason}")
        agent = d.agents.get(decision.intent)
        if agent is None:
            d.repo.transition(plan_id, "pending", "ignored")
            reply = HELP_TEXT if decision.intent == "chit_chat" else OUT_OF_SCOPE_TEXT
            await d.messenger.post(ev.channel_id, reply, thread_ts=thread_ts)
            return

        placeholder_ts = await d.messenger.post(
            ev.channel_id, "⏳ Drafting a plan…", thread_ts=thread_ts
        )
        plan = await agent.plan(raw_input=text, requester=ev.user_id, intent=decision.intent)
        plan_json = plan.model_dump_json()
        d.repo.save_plan(plan_id, plan_json)
        d.repo.audit(plan_id, "plan_generated", "system",
                     f"agent={agent.name} work_items={len(plan.work_items)}", plan_json)
        card_text, blocks = plan_card(plan_id, plan, ev.user_id)
        await d.messenger.update(ev.channel_id, placeholder_ts, card_text, blocks)
    except Exception as exc:
        log.exception("handle_event failed for %s", ev.event_id)
        d.repo.transition(plan_id, "pending", "failed")
        d.repo.audit(plan_id, "failed", "system", f"planning/agent request failed: {type(exc).__name__}", str(exc))
        try:
            if placeholder_ts:
                await d.messenger.update(
                    ev.channel_id, placeholder_ts,
                    AGENT_FAILED_TEXT if ev.source == "ask" or role_request(text, d.role_agents) else PLAN_FAILED_TEXT,
                )
            else:
                await d.messenger.post(ev.channel_id, PLAN_FAILED_TEXT, thread_ts=thread_ts)
        except Exception:
            log.exception("could not notify channel of failure")


def _authorized(user_id: str, plan_row: dict, d: Deps) -> bool:
    if user_id not in d.approver_ids:
        return False
    if d.require_separate_approver and user_id == plan_row["requester"]:
        return False
    return True


async def handle_decision(
    plan_id: str,
    decision: Literal["approve", "reject"],
    user_id: str,
    channel_id: str,
    message_ts: str,
    d: Deps,
) -> None:
    row = d.repo.get(plan_id)
    if row is None or row["plan_json"] is None:
        await d.messenger.ephemeral(channel_id, user_id, "I don't recognise that plan.")
        return
    thread_ts = row["thread_ts"]
    if not _authorized(user_id, row, d):
        d.repo.audit(plan_id, "approval_received", user_id, f"DENIED {decision}: not authorized",
                     {"user": user_id, "decision": decision})
        await d.messenger.ephemeral(
            channel_id, user_id, "You're not authorised to approve or reject plans.",
            thread_ts=thread_ts,
        )
        return

    new_state = "approved" if decision == "approve" else "rejected"
    if not d.repo.decide(plan_id, new_state, user_id):
        cur = d.repo.get(plan_id) or {}
        by = f" by <@{cur['decided_by']}>" if cur.get("decided_by") else ""
        await d.messenger.ephemeral(
            channel_id, user_id, f"This plan was already handled (state: {cur.get('state')}){by}.",
            thread_ts=thread_ts,
        )
        return
    d.repo.audit(plan_id, "approval_received", user_id, new_state,
                 {"user": user_id, "decision": decision})
    plan = Plan.model_validate_json(row["plan_json"])
    verdict = f"✅ Approved by <@{user_id}>" if decision == "approve" else f"❌ Rejected by <@{user_id}>"
    try:
        card_text, blocks = plan_card(plan_id, plan, row["requester"], outcome=verdict)
        await d.messenger.update(channel_id, message_ts, card_text, blocks)
    except Exception:
        log.exception("could not update approval card")

    if decision == "reject":
        await d.messenger.post(
            channel_id, f"Plan rejected by <@{user_id}>. Nothing was executed.", thread_ts=thread_ts
        )
        return

    try:
        result = await d.executor.execute(plan_id, plan)
        d.repo.transition(plan_id, "approved", "executed")
        d.repo.audit(plan_id, "executed", "system", result.summary,
                     {"created_items": result.created_items, "links": result.links})
    except Exception as exc:
        log.exception("execution failed for plan %s", plan_id)
        d.repo.transition(plan_id, "approved", "failed")
        d.repo.audit(plan_id, "failed", "system", f"execution failed: {type(exc).__name__}", str(exc))
        await d.messenger.post(
            channel_id, "⚠️ The plan was approved but execution failed. See the audit log.",
            thread_ts=thread_ts,
        )
        return

    text, blocks = result_message(plan, result, user_id)
    try:
        await d.messenger.post(channel_id, text, thread_ts=thread_ts, blocks=blocks)
    except Exception:
        log.exception("executed plan %s but could not post the result", plan_id)
