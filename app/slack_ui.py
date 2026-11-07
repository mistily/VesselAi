"""Block Kit rendering. Pure functions: no I/O, trivially testable."""
from __future__ import annotations

from .executor import ExecutionResult
from .schemas import Plan

ACTION_APPROVE = "plan_approve"
ACTION_REJECT = "plan_reject"

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def esc(s: str) -> str:
    """Escape Slack mrkdwn control characters in model/user supplied text."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clip(s: str, n: int = 2800) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": clip(text)}}


def _header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": clip(text, 150)}}


def _context(text: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": clip(text, 2900)}]}


def _risk_lines(plan: Plan) -> str:
    risks = sorted(plan.risks, key=lambda r: _SEVERITY_ORDER[r.severity.value])
    return "\n".join(
        f"• [{r.severity.value}] {esc(r.description)} → _{esc(r.mitigation)}_" for r in risks
    )


def plan_card(
    plan_id: str, plan: Plan, requester: str, *, outcome: str | None = None
) -> tuple[str, list[dict]]:
    """Approval card. With `outcome`, the buttons are replaced by the decision."""
    items = "\n".join(
        f"• *{esc(w.id)}* {esc(w.title)} _({esc(w.owner_role)}, {w.estimate_days:g}d)_"
        + (f" ← {esc(', '.join(w.depends_on))}" if w.depends_on else "")
        for w in plan.work_items
    )
    total = sum(w.estimate_days for w in plan.work_items)
    blocks: list[dict] = [
        _header(f"📝 {plan.title}"),
        _section(esc(plan.summary)),
        _section(f"*Work items* (~{total:g} person-days)\n{items}"),
    ]
    if plan.assumptions:
        blocks.append(_section("*Assumptions*\n" + "\n".join(f"• {esc(a)}" for a in plan.assumptions)))
    if plan.risks:
        blocks.append(_section("*Risks*\n" + _risk_lines(plan)))
    blocks.append(_section("*Next steps*\n" + "\n".join(f"{i}. {esc(s)}" for i, s in enumerate(plan.next_steps, 1))))
    blocks.append(_context(f"Requested by <@{requester}> · plan `{plan_id[:8]}`"))

    if outcome:
        blocks.append(_context(outcome))
    else:
        blocks.append(
            {
                "type": "actions",
                "block_id": f"plan_decision:{plan_id}",
                "elements": [
                    {
                        "type": "button",
                        "action_id": ACTION_APPROVE,
                        "style": "primary",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "value": plan_id,
                        "confirm": {
                            "title": {"type": "plain_text", "text": "Approve this plan?"},
                            "text": {"type": "mrkdwn", "text": "The plan will be executed immediately."},
                            "confirm": {"type": "plain_text", "text": "Approve"},
                            "deny": {"type": "plain_text", "text": "Cancel"},
                        },
                    },
                    {
                        "type": "button",
                        "action_id": ACTION_REJECT,
                        "style": "danger",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "value": plan_id,
                    },
                ],
            }
        )
    return f"Plan awaiting approval: {plan.title}", blocks[:50]


def result_message(plan: Plan, result: ExecutionResult, approver: str) -> tuple[str, list[dict]]:
    blocks: list[dict] = [_header("✅ Plan executed"), _section(result.summary)]
    if result.created_items:
        blocks.append(_section("*Created items*\n" + "\n".join(f"• {i}" for i in result.created_items)))
    if result.links:
        blocks.append(_section("*Links*\n" + "\n".join(f"• {l}" for l in result.links)))
    if plan.risks:
        blocks.append(_section("*Risks to watch*\n" + _risk_lines(plan)))
    blocks.append(_section("*Next steps*\n" + "\n".join(f"{i}. {esc(s)}" for i, s in enumerate(plan.next_steps, 1))))
    blocks.append(_context(f"Approved by <@{approver}>"))
    return f"Plan executed: {plan.title}", blocks[:50]
