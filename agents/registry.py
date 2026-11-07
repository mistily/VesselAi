"""Factory and routing helpers for Vessel AI agents."""

from __future__ import annotations

import re
from typing import Callable, Iterable, Type

from .base import AgentRuntime, BaseAgent
from .developer_copilot import DeveloperCopilotAgent
from .knowledge_agent import KnowledgeAgent
from .operations_agent import OperationsAgent
from .project_manager import ProjectManagerAgent
from .qa_reviewer import QAReviewerAgent
from .requirements_analyst import RequirementsAnalystAgent


AGENT_CLASSES: tuple[Type[BaseAgent], ...] = (
    ProjectManagerAgent,
    RequirementsAnalystAgent,
    KnowledgeAgent,
    DeveloperCopilotAgent,
    QAReviewerAgent,
    OperationsAgent,
)

# Short names are convenient for Slack's /ask command; canonical names and
# aliases are case-insensitive. Keep these explicit to avoid surprising routing.
AGENT_ALIASES: dict[str, str] = {
    "pm": "Project Manager",
    "project manager": "Project Manager",
    "requirements": "Requirements Analyst",
    "requirements analyst": "Requirements Analyst",
    "knowledge": "Knowledge Agent",
    "knowledge agent": "Knowledge Agent",
    "developer": "Developer Copilot",
    "copilot": "Developer Copilot",
    "developer copilot": "Developer Copilot",
    "qa": "QA & Reviewer",
    "reviewer": "QA & Reviewer",
    "qa reviewer": "QA & Reviewer",
    "qa & reviewer": "QA & Reviewer",
    "operations": "Operations Agent",
    "ops": "Operations Agent",
    "operations agent": "Operations Agent",
}


def list_agent_names() -> list[str]:
    """Return the names of the built-in agents in a stable order."""
    return [agent_cls.name for agent_cls in AGENT_CLASSES]


def resolve_agent_name(alias: str) -> str | None:
    """Resolve an explicit role alias to its canonical agent name."""
    normalized = " ".join(alias.lower().replace("_", " ").replace("-", " ").split())
    if normalized in AGENT_ALIASES:
        return AGENT_ALIASES[normalized]
    return next((name for name in list_agent_names() if name.lower() == normalized), None)


def parse_agent_request(text: str) -> tuple[str, str] | None:
    """Parse an explicit ``agent <role>: <request>`` or ``<role>: <request>`` prefix."""
    value = text.strip()
    if value.lower().startswith("agent "):
        value = value[6:].lstrip()
    if value.startswith("@"):
        value = value[1:]

    # Longest names first so e.g. "requirements analyst: ..." is not split early.
    for alias in sorted((*AGENT_ALIASES, *list_agent_names()), key=len, reverse=True):
        if value[: len(alias)].lower() != alias.lower():
            continue
        remainder = value[len(alias):]
        if remainder.startswith(":"):
            request = remainder[1:].strip()
        elif remainder.startswith(" - "):
            request = remainder[3:].strip()
        else:
            continue
        canonical = resolve_agent_name(alias)
        if canonical and request:
            return canonical, request
    return None


def get_agent(agent_name: str, runtime: AgentRuntime) -> BaseAgent:
    """Instantiate a named built-in agent using a provider-specific runtime."""
    canonical = resolve_agent_name(agent_name)
    for agent_cls in AGENT_CLASSES:
        if canonical == agent_cls.name:
            return agent_cls(runtime)
    raise ValueError(f"Unknown agent: {agent_name!r}")


def register_agents(runtime_factory: Callable[[], AgentRuntime]) -> dict[str, BaseAgent]:
    """Create all built-in agents with a shared runtime."""
    runtime = runtime_factory()
    return {agent_cls.name: agent_cls(runtime) for agent_cls in AGENT_CLASSES}


def iter_agents(runtime: AgentRuntime) -> Iterable[BaseAgent]:
    """Yield configured agents in a stable order."""
    for agent_cls in AGENT_CLASSES:
        yield agent_cls(runtime)


def role_request(text: str, agents: dict[str, BaseAgent]) -> tuple[BaseAgent, str] | None:
    """Return a configured agent and request when the message names a role explicitly."""
    parsed = parse_agent_request(text)
    if parsed is None:
        return None
    name, request = parsed
    agent = agents.get(name)
    return (agent, request) if agent is not None else None
