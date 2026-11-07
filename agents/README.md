# Vessel AI agents

This folder contains provider-agnostic agent definitions and workflow guidance. The Slack runtime lives in `app/`; `app/main.py` builds all six roles from the configured LLM adapter, and `app/handler.py` routes explicit role requests to them. The existing `/plan` flow remains the structured project-plan and approval workflow.

## Available roles

| `/ask` role | Role | Typical requests |
| --- | --- | --- |
| `pm` | Project Manager | Agile plans, sprint goals, risks, daily check-in prompts |
| `requirements` | Requirements Analyst | User stories, scope clarification, acceptance criteria |
| `knowledge` | Knowledge Agent | Answers grounded only in supplied evidence |
| `developer` | Developer Copilot | Implementation breakdowns, technical tradeoffs, test suggestions |
| `qa` | QA & Reviewer | Test coverage, risk-based reviews, acceptance checks |
| `operations` | Operations Agent | Drafts for reminders, calendar, Drive, and workflow automation |

Use `/ask <role> <request>` (for example, `/ask developer break this feature into reviewable tasks`) or `/ask <role>: <request>`. In a bot mention or DM, explicitly prefix the request, such as `developer: suggest tests for this workflow` or `agent knowledge: summarize these notes`. `/plan` and project-plan mentions continue to produce structured plans requiring approval before execution.

To enable `/ask`, register it as a slash command in the Slack app manifest/settings and allow Slack's command request through the existing Socket Mode app. The bot needs the applicable command/interactivity/event subscriptions and scopes for the already-supported workflows.

## Workflow and safety boundaries

- Agent role requests produce advice in the originating thread. They do not execute external actions or alter project data; proposal-style answers still require human approval before an integration layer can act.
- The structured `/plan` flow remains separate and uses the existing approval gate and audit trail.
- Agents treat messages and supplied/retrieved documents as untrusted input. Never infer insurance coverage, eligibility, pricing, or underwriting decisions from offer PDFs.
- Knowledge answers must be grounded in evidence actually supplied to the agent. Drive retrieval, Calendar operations, Gemini-specific configuration, and Whisper ingestion are future integration work; the current roles do not claim those systems were queried or changed.
- Use least-privilege credentials and avoid posting sensitive insurance or personal data in public channels.
