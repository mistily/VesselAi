# VesselAi
Flip the Switch Hackathon
Hacking started

Nov 3–7
Local Netherlands dates and times
- Kickoff: November 2, 15:30 UK time.
- Hacking: November 3, 19:31 local time.
- Submission deadline: November 7, approximately 19:29 local time.
- Teams: solo or up to four people.
- Best Business Workflow prize: $2,000.

Project: The Flip the Switch Hackathon project for Slack integrated ai automation for insurance docs

Vessel
An AI operations crew for insurance and software development

The central idea:

A developer should be able to enter a room, explain what they intend to accomplish, and have an AI team help turn that intention into an approved, traceable, completed deliverable.

This applies to:
- Insurance offer extraction and comparison.
- Insurance questionnaires for agents and customers.
- Web application development.
- Flutter application development.
- Backend/API development.
- AI integrations and automation projects.
- Client meetings, requirements and executive reporting.
I would enter the Best Business Workflow track. This is precisely the kind of practical human-and-agent collaboration the judges are looking for. They explicitly evaluate whether Switch is central to the workflow, not merely mentioned in the README. 
WeMakeDevs x DevTools Academy x Switch

The architecture
Human team

Developer · Project manager · Insurance agent · Client


Switch collaboration layer

Slack / Mattermost · Rooms · Agent identities · Shared context


Vessel Orchestrator
LangGraph or a lightweight Python orchestration service
Project Manager

Plans and delegates


Requirements Analyst

Clarifies intent


Knowledge Agent

Retrieves project evidence


Developer Copilot

Supports implementation


QA & Reviewer

Tests and validates


Operations Agent

Calendar, Drive, automation





Knowledge and execution services
RAG

Documents, decisions, code, requirements

Gemini

Reasoning, extraction, generation

Google Drive

Documents and deliverables

Google Calendar

Meetings, deadlines, reminders




Human-approved deliverables

Validated PDF · Questionnaire · Code · Tests · Reports · Client updates


One architectural distinction matters: Switch is the collaboration infrastructure, not the AI model, RAG engine or workflow automation engine. Its rooms, shared messages and agent protocol allow your custom agents to collaborate with people. Google integrations and Gemini calls should be implemented as tools exposed by your agents. 
WeMakeDevs x DevTools Academy x Switch+1

3. The business workflow: how Vessel should actually operate
I would organize the system around a single project lifecycle, rather than building a collection of unrelated chatbots.
Phase A — Listen before planning
A developer joins #project-intake and writes or dictates:
Today I want to implement the insurance offer PDF extraction module. I need to support multiple providers, identify coverage limits, exclusions, premiums and payment frequency. I want the first version tested with three sample PDFs.

Vessel responds by:
1. Transcribing voice input if necessary.
2. Extracting objectives, constraints and deliverables.
3. Checking existing project documentation.
4. Identifying dependencies and missing requirements.
5. Asking only the necessary clarifying questions.
6. Producing a proposed daily plan.
The developer confirms or corrects the plan.

This is important: the agent should not immediately start generating code just because someone described an intention.
Phase B — Agile execution copilot
Once the developer approves the plan, Vessel creates tasks.
Agent	Responsibility
Project Manager	Breaks objectives into tasks and tracks progress
Knowledge Agent	Retrieves relevant specifications and previous decisions
Developer Copilot	Provides implementation guidance and code assistance
QA Agent	Generates test cases and checks results
Reviewer	Reviews changes against acceptance criteria
Operations Agent	Updates schedules, records decisions and creates reports

Every task should have:
- An owner.
- A definition of done.
- Acceptance criteria.
- Dependencies.
- Priority.
- Status.
- Evidence of completion.
The agent should help, not silently take ownership away from the developer.
Phase C — Continuous collaboration
The interesting part is that agents should be able to join relevant project rooms.

For example:
- #insurance-pdf-engine
- #flutter-questionnaire
- #backend-api
- #qa-testing
- #client-meetings
- #project-management
The same project knowledge should remain available across those rooms, but access should depend on the user's and agent's permissions.

A developer might say:
@Vessel QA, check whether my extraction module covers the exclusions section of the Allianz specification.

The Knowledge Agent retrieves the specification, the QA Agent compares it against the implementation, and the Project Manager records the resulting task if something is missing.
Phase D — Daily executive summary
At the end of the day, Vessel generates:
- What was planned.
- What was completed.
- What remains unfinished.
- Blockers and risks.
- Decisions made.
- Work planned for tomorrow.
- Changes to delivery estimates.
The summary is posted to the project room and optionally stored in Google Drive.

4. The insurance PDF processing workflow
This is where I would make Vessel commercially useful beyond the hackathon.

Imagine an insurance agent uploads three offers into a project room.
Room: Insurance offer assessment
Workflow example

Offer_A.pdf

Insurance provider A

Uploaded

Offer_B.pdf

Insurance provider B

Uploaded

Offer_C.pdf

Insurance provider C

Uploaded


1. Document Intelligence Agent
   
   Identifies document type, provider, product, version and relevant pages.
2. Extraction Agent
   
   Extracts premiums, coverage, limits, deductibles, exclusions, waiting periods and conditions.
3. Validation Agent
   
   Checks missing fields, conflicting values, currency, units and source references.
4. Comparison Agent
   
   Builds a normalized comparison matrix and identifies material differences.
5. Insurance Analyst
   
   Produces a client-friendly assessment with advantages, disadvantages and uncertainties.
6. Human approval
   
   The agent reviews and approves the report before it is delivered.
Final deliverable

Structured JSON + Excel comparison + PDF report + source citations.

The RAG design
I would not build one giant vector database containing everything.

Use three knowledge domains:
Collection	Content
Global knowledge	Insurance terminology, regulations, product concepts
Client knowledge	Client documents, preferences, existing policies
Project knowledge	Specifications, code, meeting notes, decisions

Every extracted field should preserve provenance:
{
  "field": "annual_premium",
  "value": 1250,
  "currency": "RON",
  "source_document": "Offer_A.pdf",
  "page": 4,
  "evidence": "Prima anuală...",
  "confidence": 0.98,
  "validation_status": "verified"
}


The numbers above are illustrative.

A critical design decision: distinguish between information extracted from a contract and information inferred by an AI model. A missing exclusion must never become an assumed absence of exclusion.

For implementation, I would use:
- PDF text extraction first.
- OCR only for scanned pages.
- Structured extraction using Gemini.
- Pydantic validation.
- PostgreSQL with pgvector for retrieval.
- Original documents retained as immutable evidence.
- Page-level citations in the final report.
Use deterministic comparison rules wherever possible. Let Gemini explain differences, not invent the underlying numbers.

For real insurance deployments, add tenant isolation, encryption, access controls, retention policies and explicit human approval. Do not send identifiable client documents to an external model without an appropriate data-processing arrangement and authorization.
5. Google integrations and voice
I would separate the integration layer from Switch.
Service	Vessel responsibility
Slack	Team communication and project rooms
Google Drive API	Document ingestion, storage and deliverables
Google Calendar API	Meetings, deadlines and scheduling
Google AI Studio / Gemini API	Extraction, reasoning and generation
PostgreSQL	Projects, tasks, decisions and structured data
pgvector	Semantic retrieval
Python services	PDF processing, validation and automation

A few useful automations:

Google Drive
- Watch designated project folders.
- Detect new or updated PDFs.
- Register document versions.
- Start extraction.
- Save validated reports.
Google Calendar
- Schedule approved meetings.
- Generate agendas using project context.
- Prepare meeting summaries.
- Turn agreed action items into tasks.
- Remind owners about deadlines.
Slack
- Allow users to invoke agents through mentions.
- Let agents communicate with one another.
- Maintain task discussions in their relevant rooms.
- Escalate important decisions to humans.
Don't give every agent unrestricted access to every integration. Use scoped credentials and tool permissions.
About your free Whisper month
One small clarification: do you mean OpenAI Whisper or Wispr Flow?

They are different technologies:
- OpenAI Whisper is speech recognition: voice to text.
- Wispr Flow is a voice-dictation product and is also the hackathon's voice-building side-track.
For executive summaries that are read aloud, you additionally need text-to-speech (TTS). For recorded meetings, Whisper can transcribe them before the summarization agent processes the transcript.

There is an opportunity to enter the $500 Code with Wispr side-track as well, if your free month is actually Wispr Flow. It requires a usage scorecard screenshot
