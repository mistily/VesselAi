from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Intent = Literal["project_plan", "chit_chat", "out_of_scope"]
INTENTS: tuple[str, ...] = ("project_plan", "chit_chat", "out_of_scope")


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class WorkItem(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,20}$")
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=600)
    owner_role: str = Field(default="unassigned", max_length=60)
    estimate_days: float = Field(ge=0, le=365)
    depends_on: list[str] = Field(default_factory=list)


class Risk(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    severity: Severity
    mitigation: str = Field(min_length=1, max_length=300)


class Plan(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=600)
    assumptions: list[str] = Field(default_factory=list, max_length=10)
    work_items: list[WorkItem] = Field(min_length=1, max_length=25)
    risks: list[Risk] = Field(default_factory=list, max_length=10)
    next_steps: list[str] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def _check_graph(self) -> "Plan":
        ids = [w.id for w in self.work_items]
        if len(set(ids)) != len(ids):
            raise ValueError("work item ids must be unique")
        graph = {w.id: w.depends_on for w in self.work_items}
        for wid, deps in graph.items():
            missing = [d for d in deps if d not in graph]
            if missing:
                raise ValueError(f"{wid} depends on unknown ids: {missing}")

        visit_state: dict[str, int] = {}  # 1 = in progress, 2 = done

        def visit(node: str) -> None:
            if visit_state.get(node) == 1:
                raise ValueError(f"dependency cycle involving {node}")
            if visit_state.get(node) == 2:
                return
            visit_state[node] = 1
            for nxt in graph[node]:
                visit(nxt)
            visit_state[node] = 2

        for node in graph:
            visit(node)
        return self


@dataclass(frozen=True)
class PlanRequest:
    """Provider-agnostic input to LLMAdapter.generate()."""

    intent: str
    raw_input: str
    requester: str
    system_prompt: str
    user_prompt: str
