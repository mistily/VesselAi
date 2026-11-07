"""Vessel router: cheap rule gate first, LLM classification only when ambiguous."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from .schemas import Intent

log = logging.getLogger(__name__)

MENTION_RE = re.compile(r"<@[A-Z0-9]+>")
CHITCHAT_RE = re.compile(
    r"(hi|hello|hey|yo|thanks|thank you|thx|good (morning|afternoon|evening)|help|"
    r"who are you|what can you do)[\s!.?]*",
    re.I,
)
PLANNING_RE = re.compile(
    r"\b(plan|planning|roadmap|milestones?|break\s*down|project|timeline|sprint|scope|"
    r"kick-?off|launch|backlog|rollout|migration|deliverables?)\b",
    re.I,
)
OUT_OF_SCOPE_RE = re.compile(
    r"\b(weather|joke|poem|lyrics|horoscope|stock price|recipe|translate|trivia)\b", re.I
)


def clean_text(text: str) -> str:
    return MENTION_RE.sub("", text or "").strip()


class Classifier(Protocol):
    async def classify(self, text: str) -> Intent: ...


@dataclass(frozen=True)
class RouteDecision:
    intent: Intent
    via: Literal["rule", "llm", "command"]
    reason: str


class VesselRouter:
    def __init__(self, classifier: Classifier | None = None) -> None:
        self._classifier = classifier

    async def route(self, text: str, source: str = "mention") -> RouteDecision:
        text = text.strip()
        if not text:
            return RouteDecision("chit_chat", "rule", "empty message")
        if source == "command":  # /plan is an explicit planning request
            return RouteDecision("project_plan", "command", "slash command")
        if CHITCHAT_RE.fullmatch(text):
            return RouteDecision("chit_chat", "rule", "greeting/help")

        planning = bool(PLANNING_RE.search(text))
        out_of_scope = bool(OUT_OF_SCOPE_RE.search(text))
        if planning and not out_of_scope:
            return RouteDecision("project_plan", "rule", "planning keywords")
        if out_of_scope and not planning:
            return RouteDecision("out_of_scope", "rule", "out-of-scope keywords")

        # Ambiguous (no signal, or conflicting signals) -> ask the LLM.
        if self._classifier is None:
            return RouteDecision("out_of_scope", "rule", "ambiguous, no classifier configured")
        try:
            intent = await self._classifier.classify(text)
            return RouteDecision(intent, "llm", "llm classification")
        except Exception as exc:  # fail closed: never plan on a failed classification
            log.warning("classifier failed: %s", exc)
            return RouteDecision("out_of_scope", "llm", "classifier failed (fail closed)")
