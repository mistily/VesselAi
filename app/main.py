from __future__ import annotations

import logging

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from .config import Settings
from .executor import SummaryExecutor
from .handler import Deps
from .llm import build_adapter
from .messenger import SlackMessenger
from .pm_agent import PMAgent
from .repository import PlanRepository
from .router import VesselRouter
from .slack_app import register_handlers

log = logging.getLogger("switch_planner")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()

    repo = PlanRepository(settings.db_path)
    orphans = repo.fail_orphans()
    if orphans:
        log.warning("marked %d orphaned plan(s) as failed", orphans)

    adapter = build_adapter(settings)
    app = AsyncApp(token=settings.slack_bot_token)
    deps = Deps(
        repo=repo,
        messenger=SlackMessenger(app.client),
        router=VesselRouter(classifier=adapter),
        agents={"project_plan": PMAgent(adapter)},
        executor=SummaryExecutor(),
        approver_ids=settings.approver_ids,
        require_separate_approver=settings.require_separate_approver,
    )
    register_handlers(app, deps)

    if not settings.approver_ids:
        log.warning("APPROVER_USER_IDS is empty: no one can approve plans (fail closed)")

    handler = AsyncSocketModeHandler(app, settings.slack_app_token)
    try:
        await handler.start_async()
    finally:
        await adapter.aclose()
        repo.close()
