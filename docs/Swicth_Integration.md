# Vessel — Multi-Agent Development Team Powered by Switch

Vessel is an experimental AI-powered software development team built for the WeMakeDevs SWITCH Hackathon.

The project explores how multiple specialized coding agents can collaborate through Switch Rooms, using a shared communication channel to coordinate planning, implementation, quality assurance, and development workflows.

## 1. How Switch Was Used

Switch serves as the communication and orchestration layer between our AI agents.

Instead of operating as independent chatbots, the agents are connected to a shared room where they can receive messages, follow discussions, and coordinate work according to their assigned responsibilities.

The implementation uses:

- **Switch Console v0.40.1** for agent configuration and session management.
- **Codex** as the coding-agent runtime.
- **Switch Rooms** for agent communication and collaboration.
- **Slack** as the team's communication interface.
- **Git and GitHub** for source control.

Switch Console manages the agent sessions and provides the Switch skill and session-local MCP tools.

## 2. Connected Agents

The current configuration includes four Codex agents managed through Switch Console.

| Agent | Responsibility |
|---|---|
| Vessel PM | Project planning, task decomposition, prioritization, and acceptance criteria |
| Vessel QA | Quality assurance, testing, issue identification, and validation |
| Vessel RA | Requirements Analyst	User stories, scope clarification, acceptance criteria
| Vessel KA | Knowledge Agent	Answers grounded only in supplied evidence
| Vessel DC | Developer Copilot	Implementation breakdowns, technical tradeoffs, test suggestions
| Vessel OP | Operations Agent	Drafts for reminders, calendar, Drive, and workflow automation

### Vessel PM

The project management agent translates project objectives into actionable development tasks.

Its responsibilities include defining requirements, prioritizing work, proposing acceptance criteria, and coordinating progress.

### Vessel QA

The quality assurance agent reviews implementation outcomes, identifies defects, and helps evaluate whether completed work satisfies the project's requirements.

### Additional Agents

The remaining agents extend the team with specialized responsibilities, such as implementation, technical review, or workflow coordination.

Their exact roles depend on the configured agent instructions.

## 3. Channel and Room Setup

The collaboration environment uses Slack together with Switch Rooms.

**Communication configuration:**

- Communication platform: Slack
- Switch room: Vessel-Slack 2 rooms: #C0CEQ7LP3K9, #D0CFPMSHM8Q
- Slack channel: vessel-team
- Agent runtime: Codex
- Agent management: Switch Console

The intended workflow is:

1. A developer submits a request through the connected communication environment.
2. Switch delivers the relevant room message to an addressed agent.
3. The agent processes the request according to its role.
4. Agents use Switch MCP tools to interact with the room and coordinate subsequent work.
5. Development outcomes are reviewed and tracked through the project workflow.

Switch's watcher handles room events and message delivery, while the session-local MCP server provides tools for room operations.

## 4. Architecture

```text
Developer / Team
       |
       v
Slack / Switch Room
       |
       v
Switch Console
       |
       +-- Vessel PM (Codex)
       |
       +-- Vessel QA (Codex)
       |
       +-- Agent 3 (Codex)
       |
       +-- Agent 4 (Codex)
       |
       v
Switch Agent Bridge
       |
       v
Room Operations / MCP Tools
```

Each agent has a Switch-managed session. Switch Console delivers room messages and supplies the session with the Switch skill and an authenticated local MCP endpoint.

The agent's MCP calls are forwarded through its session host and watcher to the Switch operations registry.

## 5. How to Run

### Prerequisites

- Windows 11 or another Switch-supported environment
- Switch Console
- Codex CLI with an authenticated account
- Git
- Access to the project's Slack workspace and Switch environment

### Step 1 — Clone the repository

```bash
git clone  https://github.com/mistily/VesselAi.git
cd VesselAi
```

### Step 2 — Start Switch Console

Open Switch Console and sign in to the configured Switch environment.

Ensure the local Switch services are running.

### Step 3 — Configure the agents

Create or select the four Codex agents.

Assign each agent its role-specific instructions and the appropriate working directory.

Switch Console manages the session integration, including the Switch skill and local MCP registration.

### Step 4 — Connect the communication room

Open the configured Switch room and connect the relevant agents.

Use the Slack channel configured for team communication, where applicable.

### Step 5 — Start agent sessions

Launch the agents through Switch Console.

Verify that they are connected and can receive addressed room messages.

### Step 6 — Test the workflow

Send a message to the project management or QA agent.

Example:

> @Vessel QA Please review the current implementation and identify the highest-priority testing tasks.

Verify that the agent receives the request and responds.

For complete integration testing, also verify that the agent can successfully invoke Switch room tools.

## 6. Current Implementation Status

The following functionality has been observed:

- Four Codex agents configured through Switch Console.
- Codex sessions launched successfully.
- Switch room messages delivered to agents.
- Agents able to process incoming messages and generate responses.
- Git CLI installed and operational.

### Known limitation: MCP tool initialization

During testing with Switch Console v0.40.1 on Windows 11, the session-local `switch` MCP server failed to initialize in Codex.

The observed error was:

```text
MCP server startup failed
server_name="switch"
handshaking with MCP server failed
HTTP request failed:
error decoding response body
```

The issue persisted after restarting Switch Console.

The Codex SDK logs also showed response-decoding failures involving `codex_apps`.

Consequently, successful message delivery has been verified, but full agent-to-room tool interaction has not yet been confirmed.

The problem has been reported to the Switch maintainers.

This limitation is documented to distinguish implemented functionality from the intended multi-agent collaboration workflow.

## 7. Security and Privacy

- Agent credentials are managed by Switch.
- Local MCP communication uses authenticated loopback endpoints.
- API keys and bearer tokens must not be committed to Git.
- Local `.switch/` credential directories should remain excluded from version control.
- Private Slack messages, agent logs, and sensitive project files should not be included in public submissions.

## 8. Future Development

Planned improvements include:

- Reliable agent-to-agent collaboration through Switch MCP tools.
- Automated sprint planning and task assignment.
- AI-assisted code reviews and QA workflows.
- Integration with project documentation.
- Automated progress summaries and daily standups.
- Human approval for consequential development actions.

## 9. Technologies

**Agent orchestration:** Switch Rooms, Switch Console  
**AI runtime:** Codex  
**Communication:** Slack  
**Version control:** Git, GitHub  
**Development environment:** Windows 11

## 10. Hackathon

Built for the WeMakeDevs SWITCH Hackathon.

Vessel demonstrates an approach to building a specialized, collaborative AI development team, with Switch providing the communication infrastructure between agents.

Built for the **WeMakeDevs SWITCH Hackathon**.

Vessel demonstrates an approach to building a specialized, collaborative AI development team, with Switch providing the communication infrastructure between agents.
