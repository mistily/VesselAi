"""Execution seam. Runs only after an approved decision.

The default executor performs no external side effects (integrations are out of scope);
it finalises the approved plan into a summary. To add Jira/GitHub/Notion later, implement
Executor and pass it in main.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .schemas import Plan


@dataclass
class ExecutionResult:
    summary: str
    created_items: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)


class Executor(Protocol):
    async def execute(self, plan_id: str, plan: Plan) -> ExecutionResult: ...


class SummaryExecutor:
    async def execute(self, plan_id: str, plan: Plan) -> ExecutionResult:
        total = sum(w.estimate_days for w in plan.work_items)
        items = [
            f"*{w.id}* {w.title} ({w.owner_role}, {w.estimate_days:g}d)" for w in plan.work_items
        ]
        return ExecutionResult(
            summary=f"*{plan.title}* is approved and recorded: {len(items)} work items, "
            f"~{total:g} person-days (plan `{plan_id[:8]}`).",
            created_items=items,
        )
