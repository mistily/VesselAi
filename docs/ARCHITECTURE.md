# VesselAI — Architecture and implementation plan

> Status: **proposed architecture**, not a description of a deployed implementation. The GitHub repository currently provides only a brief README and Python-oriented .gitignore. Switch Console, Slack, Codex and Cursor observations below are based on local troubleshooting, not committed source code.

## Purpose

VesselAI is a human-supervised, Slack-integrated AI workflow for insurance-document processing and software delivery coordination. The initial goal is to help a small team (including a solo operator) capture requests, extract information from insurance documents, organize implementation work, and produce reviewable outputs.

## Logical components

1. **Slack / Switch interface** — receive requests, route messages to authorized agents, and return responses to the correct room.
2. **Agent orchestration** — select an agent, create a session, inject permitted tools and context, enforce room membership, and record outcomes.
3. **Document intake** (planned) — ingest PDF files from approved sources, identify document type, and maintain file provenance.
4. **Extraction and validation** (planned) — OCR where needed, structured field extraction, schema validation, evidence pointers and uncertainty flags.
5. **Human review** (planned) — require approval before externally visible decisions, policy recommendations, or edits to client data.
6. **Audit trail** (planned) — retain minimal event metadata, tool usage, source references, and review decisions, with retention controls.

## Agent roles

| Role | Responsibility | Permission boundary |
| --- | --- | --- |
| Vessel PM | Scope, requirements, priorities, acceptance criteria, status summaries | Read project context; do not edit files without explicit authorization |
| Vessel QA | Test plans, acceptance checks, defect reports, review of evidence | Read approved project/test materials; no broad home-directory access |
| Document processor (planned) | Extract and validate insurance-document fields | Only approved input documents; no autonomous submission |
| Reviewer (planned) | Validate outputs, contradictions, missing citations | Escalate uncertainty; no autonomous binding insurance advice |

The exact agent-to-provider assignments and runtime configuration should be confirmed against Switch, not inferred from this document.

## Suggested processing flow

```text
Approved document / Slack request
        |
        v
Access check + intake metadata
        |
        v
Classification + extraction
        |
        v
Schema validation + source references
        |
        v
Agent review / QA checks
        |
        v
Human approval gate
        |
        v
Slack summary / export / authorized action
```

## Proposed data entities

- `Document`: id, source, filename, content hash, uploaded_at, retention_class
- `Extraction`: document_id, schema_version, fields, evidence_locations, confidence_flags
- `Task`: id, request_origin, assignee, status, acceptance_criteria
- `AgentRun`: id, agent_id, provider, room_id, start/end, result, error_category
- `Approval`: artifact_id, reviewer, decision, timestamp
- `AuditEvent`: actor, action, resource_id, outcome, timestamp

## Nonfunctional requirements

- Least-privilege file access and isolated project workspace
- No default access to Obsidian, journals, sketches, or unrelated directories
- No credentials, client documents, or chat transcripts committed to Git
- Redaction of sensitive material in logs
- Explicit human review of insurance-related outputs
- Reproducible local setup with resource limits appropriate for an 8 GB RAM laptop
- Graceful failure when Switch Core, Slack, or a provider is unavailable

## Implementation order

1. Stabilize agent startup, room membership, and Switch tool availability.
2. Implement a minimal end-to-end Slack request → agent response → audit event.
3. Add a synthetic insurance PDF and deterministic schema validation.
4. Add human review and export.
5. Add authenticated external document sources only after access and retention policies are tested.
