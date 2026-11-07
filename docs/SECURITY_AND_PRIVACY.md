# Security and privacy baseline

> Proposed policy for VesselAI. This document does not assert that all controls are implemented.

## Threat model

The system may handle insurance documents, client identifiers, financial information, internal Slack messages, and developer credentials. Agent tools can potentially reach files beyond the intended workspace unless constrained by a real sandbox.

## Required controls

1. **Workspace isolation:** Agents operate in a dedicated project directory with filesystem permissions restricted to that directory. Ignore files such as `.cursorignore` are not security boundaries.
2. **Least privilege:** Each agent receives only the necessary read/write/tool capabilities. Separate read-only planning from authorized modification.
3. **Source allowlist:** Access only explicitly approved document sources and repositories. No exploratory scanning of the user's home directory.
4. **Human approval:** Require review before transmitting client data, publishing outputs, editing code, or acting on insurance decisions.
5. **Data minimization:** Prefer synthetic samples during development. Redact personal data from prompts, logs, issue reports, and commits.
6. **Credential hygiene:** Keep tokens in OS credential stores or approved secret managers; never in source files or shared transcripts.
7. **Auditability:** Record agent identity, provider, tool name, authorized scope, outcome, and reviewer decision, without copying sensitive document contents into general-purpose logs.
8. **Retention:** Define deletion periods for uploads, extracted data, logs, and backups. Make deletion of local and remote copies distinct.
9. **Incident response:** Disable the agent, revoke OAuth integrations, terminate active processes, preserve relevant logs, review access history, and rotate affected credentials where warranted.

## Known local privacy incident to investigate

During development, a Cursor agent reportedly discovered personal Obsidian vault material, sketches, and journal content unrelated to the task. The extent of file reading and remote transmission has **not been established**.

Actions discussed in troubleshooting included removing the Cursor-backed Switch agent, revoking GitHub authorization, and disabling the separate Cursor CLI installation. Verify completion of each action independently.

## Insurance-specific safeguards

- Treat extracted policy terms as unverified until checked against the source document.
- Retain page/section evidence for every material field.
- Flag missing exclusions, coverage limits, effective dates, and ambiguous clauses.
- Never represent a model-generated coverage determination as insurer approval.
- Assess applicable GDPR obligations and data-processing agreements before using real customer data or external AI providers.

## Pre-release checklist

- [ ] Test filesystem sandbox against attempts to read unrelated directories
- [ ] Verify provider permissions and external OAuth grants
- [ ] Validate synthetic-document extraction with reproducible tests
- [ ] Verify access control for Slack rooms and agent sessions
- [ ] Review retention, deletion, and log-redaction behavior
- [ ] Require human approval for sensitive operations
- [ ] Document supported deployments and incident-response owner
