# Local setup and troubleshooting

> This document captures **observed local troubleshooting**, not a guaranteed installation guide for Switch. Verify paths and commands against your installation.

## Current environment

- Windows 11 with an 8 GB RAM laptop
- Switch Console and a native local Switch server
- Slack/Mattermost-style room messaging
- Codex CLI tested independently
- Cursor CLI previously installed but slated for removal due to usage-limit and privacy concerns

No runnable application dependency manifest has yet been confirmed in this GitHub repository.

## Known observations

| Symptom | Evidence | Interpretation |
| --- | --- | --- |
| Agent shows “Thinking” and returns nothing | Switch Console logs reported fetch failures to localhost:12385 | Core connectivity was intermittent; a one-time TCP success is not proof of stability |
| Session placement rejected | Agent `cff76414-1fda-4b03-9acb-f25f69a7deb6` was not a member of the requested room | Check actual room membership and placement, not just provider credentials |
| Cursor session error | `JsonRpcError: Invalid params` | Could indicate incompatible or malformed session parameters; root cause unconfirmed |
| Cursor standalone invocation | `ActionRequiredError: You've hit your usage limit` | Cursor account cannot currently run additional Agent requests |
| QA agent reports no Switch tools | Agent generated text but said Switch tools unavailable | Tool exposure/injection or permissions require verification |
| PostgreSQL admin launch | Native PostgreSQL rejected administrative execution | Run Switch normally, not as administrator |

## Read-only diagnostics

Check local server reachability:

```powershell
Test-NetConnection localhost -Port 12385 |
  Select-Object ComputerName, RemotePort, TcpTestSucceeded
```

Inspect recent Switch Console errors:

```powershell
Get-Content "$env:APPDATA\switchdash\logs\switch-console.log" -Tail 150 |
  Select-String -Pattern 'error|failed|session|grant|placement'
```

Inspect the local server log:

```powershell
Get-Content "$env:APPDATA\switchdash\local-switch-server\native\logs\switch-core.log" -Tail 80
```

Do not publish raw logs: they can contain filesystem paths, room IDs, prompts, or other sensitive data.

## Troubleshooting sequence

1. Confirm the Switch Core is consistently reachable, not merely briefly listening.
2. Confirm the intended agent is a member of the destination room.
3. Confirm its provider is available and within usage limits.
4. Confirm Switch skills/tools are actually present inside the agent session.
5. Correlate timestamps between logs (Switch UTC timestamps versus PostgreSQL local time).
6. Re-test with a harmless `READY` message; record delivery and tool-access outcomes separately.

Avoid deleting `%APPDATA%\switchdash\agent-controller`, editing watcher configuration files, resetting PostgreSQL, or restarting unrelated Docker containers as first-line diagnostics.

## Outstanding verification

- Whether a successful Codex session can post directly to its authorized room
- Whether agent-specific Switch skills are injected correctly
- Whether the native Switch server remains stable under local resource pressure
- Which configuration is authoritative for provider registration and watcher lifecycle
