"""Factory and registry helpers for Vessel AI agents."""

from __future__ import annotations

from typing import Callable, Iterable, Type

from .base import AgentRuntime
from .developer_copilot import DeveloperCopilotAgent
from .knowledge_agent import KnowledgeAgent
from .operations_agent import OperationsAgent
from .project_manager import ProjectManagerAgent
from .qa_reviewer import QAReviewerAgent
from .requirements_analyst import RequirementsAnalystAgent
from .base import BaseAgent


AGENT_CLASSES: tuple[Type[BaseAgent], ...] = (
    ProjectManagerAgent,
    RequirementsAnalystAgent,
    KnowledgeAgent,
    DeveloperCopilotAgent,
    QAReviewerAgent,
    OperationsAgent,
)


def list_agent_names() -> list[str]:
    """Return the names of the built-in agents in a stable order."""
    return [agent_cls.name for agent_cls in AGENT_CLASSES]


def get_agent(agent_name: str, runtime: AgentRuntime) -> BaseAgent:
    """Instantiate the named agent with the supplied runtime.

    Args:
        agent_name: Name matching the agent's `name` attribute.
        runtime: A provider-specific runtime implementation.

    Returns:
        A configured agent instance.

    Raises:
        ValueError: If the requested agent is not known.
    """
    for agent_cls in AGENT_CLASSES:
        if agent_cls.name.lower() == agent_name.strip().lower():
            return agent_cls(runtime)
    raise ValueError(f"Unknown agent: {agent_name!r}")


def register_agents(runtime_factory: Callable[[], AgentRuntime]) -> dict[str, BaseAgent]:
    """Create a registry of agent instances from a runtime factory.

    This keeps agent creation centralized and makes tests or CLI bootstrapping easy.
    """
    runtime = runtime_factory()
    return {agent_cls.name: agent_cls(runtime) for agent_cls in AGENT_CLASSES}


def iter_agents(runtime: AgentRuntime) -> Iterable[BaseAgent]:
    """Yield configured agent instances in a stable order."""
    for agent_cls in AGENT_CLASSES:
        yield agent_cls(runtime)
