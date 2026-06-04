# Implementation Audit — Current Evidence Snapshot

This file summarizes the implementation status of the repository at the time of the audit.

Important: this is a current evidence snapshot, not a permanent final state. If the code evolves before submission, this file should be updated or superseded by a newer audit.

RFQ Management System — Implementation Status Report
This report is based on direct inspection of the repository at d:/RFQ_MANAGEMENT_SYSTEM (branch feat/rfq-copilot-batch10-v2-threads-working-memory). Nothing in the code was modified.

1. Global project structure
The repository is a polyrepo-in-monorepo: three Python microservices and one Next.js frontend.

Path	Role
microservices/rfq_manager_ms/	RFQ lifecycle backend (FastAPI). Owns RFQs, workflows, stages, subtasks, notes, files, reminders, stats/analytics.
microservices/rfq_copilot_ms/	Conversational copilot backend (FastAPI). Two parallel API lanes (v1 grounded reply, v2 trust-boundary pipeline).
microservices/rfq_intelligence_ms/	Intelligence/parser backend (FastAPI). MR-package ZIP parser, workbook (Excel) parser, briefing/snapshot artifacts.
frontend/rfq_ui_ms/	Next.js 15 / React 18 web client.
docs/agent_context/	Cross-cutting agent docs (top-level).
scripts/rfqmgmt_scenario_stack.py	Scenario orchestration script across services.
seed_outputs/	Scenario seed artifacts.
Per-service auxiliary folders exist for each backend service: migrations/, tests/, docs/, scripts/, Dockerfile, alembic.ini, pytest.ini, requirements*.txt. Docker Compose files are per-service (microservices/rfq_intelligence_ms/docker-compose.yml, microservices/rfq_intelligence_ms/docker-compose.scenario.yml, microservices/rfq_manager_ms/docker-compose.scenario.yml). No top-level/root docker-compose orchestrates the three services together. Copilot has only a Dockerfile, no compose file.

2. Technology stack
Common backend (all three services): Python, FastAPI 0.115.0, Uvicorn 0.30.0, SQLAlchemy 2.0.35, Pydantic 2.9, Pydantic-Settings 2.5, httpx 0.27.0, python-dotenv 1.0.1. CI is pinned to Python 3.11 (microservices/rfq_manager_ms/.github/workflows/ci.yml:21).

Service	DB / ORM	Notable libs	Docker
rfq_manager_ms	psycopg2-binary 2.9.9 + Alembic 1.13.2; SQLAlchemy declarative models. Postgres in compose. Prometheus client 0.22.1; python-multipart for uploads.	Alembic migrations chain present (migrations/versions/*.py).	Dockerfile + docker-compose.scenario.yml.
rfq_copilot_ms	SQLite by default (DATABASE_URL: str = "sqlite:///./rfq_copilot.db" — src/config/settings.py:10). Base.metadata.create_all on startup (src/app.py:82-90) — Alembic folder exists but versions/ is empty.	openai==1.54.0 for Azure OpenAI.	Dockerfile only. No compose.
rfq_intelligence_ms	psycopg2-binary 2.9.9 + Alembic 1.13.2; 4 migrations applied.	xlrd==2.0.1, openpyxl==3.1.5, python-docx==1.1.2 for parsing.	Dockerfile + docker-compose.yml + docker-compose.scenario.yml.
rfq_ui_ms	n/a (no DB)	Next.js ^15.5.15, React ^18.3.1, TypeScript ^5.4.5, Tailwind 3.4, framer-motion 11.2, Radix UI primitives, lucide-react.	No Dockerfile.
LLM provider: Azure OpenAI is the only provider. Configured via env keys AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT, AZURE_OPENAI_INTENT_DEPLOYMENT — see src/config/settings.py:24-29. The repo references "GPT-4o" by name in code comments (e.g. src/connectors/llm_connector.py:1). The actual deployed model name is whatever the deployment string points to — the repo defines no specific model literal, only the deployment env var.

3. Manager service status (rfq_manager_ms)
Path / framework: microservices/rfq_manager_ms, FastAPI 0.115.0. App factory at src/app.py:41. All v1 routes mounted under /rfq-manager/v1.
Title/version: rfq_manager_ms v1.0.0 (src/app.py:50-54).
Endpoints by family (counted from the route files)
Family	Endpoints (paths)	Source
RFQs (8)	POST /rfqs, GET /rfqs, GET /rfqs/export, GET /rfqs/stats, GET /rfqs/analytics, GET /rfqs/by-code/{rfq_code}, GET /rfqs/{rfq_id}, PATCH /rfqs/{rfq_id}, POST /rfqs/{rfq_id}/cancel	src/routes/rfq_route.py
Workflows (3)	GET /workflows, GET /workflows/{id}, PATCH /workflows/{id}	src/routes/workflow_route.py
RFQ Stages (7)	GET /rfqs/{id}/stages, GET /rfqs/by-code/{code}/stages, GET /rfqs/{id}/stages/{sid}, PATCH /rfqs/{id}/stages/{sid}, POST .../notes, POST .../files, POST .../advance	src/routes/rfq_stage_route.py
Subtasks (4)	POST/GET .../subtasks, PATCH/DELETE .../subtasks/{id}	src/routes/subtask_route.py
Files (3)	GET .../stages/{sid}/files, GET /files/{id}/download, DELETE /files/{id}	src/routes/file_route.py
Reminders (8)	POST/GET /reminders, GET /reminders/stats, GET /reminders/rules, PATCH /reminders/rules/{id}, POST /reminders/test, POST /reminders/process, POST /reminders/{id}/resolve	src/routes/reminder_route.py
Health/metrics	GET /health, GET /metrics (Prometheus)	src/app.py:184-191
Endpoint count: ~33 declared route handlers (release notes claim "31 documented endpoints" — RELEASE_v1.0.0.md:7).

Domain model (from src/models/)
RFQ, RFQStage, Workflow, StageTemplate, Subtask, RFQNote, RFQFile, Reminder (plus ReminderRule), RfqCodeCounter, RFQHistory (declared but dormant in V1 per docs/KNOWN_LIMITATIONS.md:15), RfqStageFieldValue (also dormant in V1, same source).

Workflow templates
Loaded by seed script + Alembic migrations — not from the database content alone, not from a runtime config file, and not hardcoded in business logic. The catalog (GHI-LONG, GHI-SHORT, GHI-CUSTOM) is defined in scripts/bootstrap_base_data.py:20-69 and seeded into the DB. Workflows table at runtime is the source of truth (src/models/workflow.py).

Lifecycle / stages
Stage progression exists with status transitions, terminal-stage freezing, and current_stage_id tracking — src/utils/rfq_lifecycle.py (validate_rfq_status_transition, apply_terminal_stage_freeze, calculate_rfq_lifecycle_progress). Status whitelist at src/utils/rfq_status.py.
Mandatory field validation: RfqStageController._validate_mandatory_fields (rfq_stage_controller.py:579) parses stage.mandatory_fields (comma-separated snapshot from template) and is invoked in advance (line 229).
Blockers: fields on rfq_stage, NOT a separate entity. Columns blocker_status (Blocked/Resolved/null) and blocker_reason_code (src/models/rfq_stage.py:89-90). Logic in rfq_stage_controller.py:366-434.
Subtasks: full CRUD; soft delete via deleted_at column (src/models/subtask.py:48). Endpoint comment says "Auto-updates parent stage progress" (subtask_route.py:54).
Notes: append-only — RFQNote has only created_at, no updated_at, and the route says "(append-only)" (rfq_stage_route.py:99).
Files: upload (multipart), list, download (FileResponse stream), soft delete. Storage helpers in src/utils/file_storage.py; uploads/ folder present.
Reminders / reminder rules: Reminder and ReminderRule models; endpoints for create/list/stats/list rules/toggle rule/test/process/resolve. test route comment: "Test reminder email (log-only in V1)" (reminder_route.py:85). Bootstrap script seeds reminder rules.
Stats / analytics: real DB queries against the rfq and rfq_stage tables — src/datasources/rfq_datasource.py:209-324. get_stats returns true counts and computed avg cycle days. get_analytics returns a real win rate from awarded/lost counts and per-client breakdown by group-by. Margin and estimation-accuracy fields are returned as None until reliable source data exists (line 318-323).
Auth / IAM: bearer-token resolution via src/connectors/iam_service.py; bypass mode (AUTH_BYPASS_ENABLED default False — src/config/settings.py:30) and per-permission decorators (src/utils/auth.py).
Event publication: EventBusConnector publishes domain events over HTTP to EVENT_BUS_URL (src/connectors/event_bus.py). Per KNOWN_LIMITATIONS.md:14: "intentionally minimal (HTTP best-effort, post-commit) and is not yet a durable outbox/retry architecture."
Tests: pytest, 25 unit + 2 integration files at tests/unit/ and tests/integration/. Coverage spans rfq lifecycle, stage controller, subtask, workflow, reminder, file roundtrip, auth bypass/enforcement, observability, pagination, code-generation atomicity, scenario seed.
Postman: two collections at docs/postman/ (*_full_walkthrough_v2.json, *_full_walkthrough_env_v2.json).
Container: Dockerfile + scenario compose. Manager has no standalone docker-compose.yml (only the scenario variant).
Known limitations (verbatim from docs/KNOWN_LIMITATIONS.md): event publication minimal; rfq_history and rfq_stage_field_value dormant; observability minimal (no full tracing); deployment baseline is Compose only. From RELEASE_v1.0.0.md: "LG-06: RFQ code generation is still non-atomic under high concurrency"; "Out of scope for v1.0.0: Full IAM integration and production auth enforcement, Intelligence logic, Chatbot logic, Frontend/UI work."
4. Copilot service status (rfq_copilot_ms)
Path / framework: microservices/rfq_copilot_ms, FastAPI; title rfq_copilot_ms v0.3.0 (src/app.py:62-66). Two API lanes:
/rfq-copilot/v1 — legacy MVP lane.
/rfq-copilot/v2 — frozen v4 trust-boundary architecture (Slice 1 active per docstring src/app.py:12-23).
Routes
Route	Source
POST /rfq-copilot/v1/threads/open and /threads/new	src/routes/entry_routes.py
POST /rfq-copilot/v1/threads/{id}/turn	src/routes/turn_routes.py
POST /rfq-copilot/v2/threads/new, /open, /list, GET /{id}	src/routes/v2/thread_routes.py
POST /rfq-copilot/v2/threads/{id}/turn	src/routes/v2/turn_routes.py
GET /health	src/routes/health_routes.py
Thread management: implemented in v1 and v2 — create new, open-or-resume, list, load by id with reconstructed messages (src/routes/v2/thread_routes.py; src/datasources/v2_thread_datasource.py; src/datasources/v2_history_datasource.py).

Turn endpoint: implemented on both lanes — full pipeline orchestration in src/controllers/v2_turn_controller.py:138-243.

v4 pipeline components (each as its own module under src/pipeline/)
Component	File	Notes
FastIntake (deterministic regex)	pipeline/fast_intake.py + fast_intake_patterns.py	Anchored regex enforced by anti-drift test.
LLM Planner	pipeline/planner.py	Azure OpenAI; structured output.
Planner Validator	pipeline/planner_validator.py	
ExecutionPlanFactory	pipeline/execution_plan_factory.py	Sole constructor of TurnExecutionPlan (anti-drift enforced).
Path registry (config)	src/config/path_registry.py (PATH_CONFIGS) and types src/models/path_registry.py	Reader allowlist enforced (factory + gate only).
EscalationGate	pipeline/escalation_gate.py	Routes failures to Path 8.x safe templates.
Resolver / Access / ToolExecutor	pipeline/resolver.py, access.py, tool_executor.py	
Evidence Check	pipeline/evidence_check.py	
Context Builder	pipeline/context_builder.py	
Path 4 deterministic renderer	pipeline/path4_renderer.py	
Compose (LLM draft)	pipeline/compose.py	Used for summary/blockers synthesis intents.
Guardrails (deterministic)	pipeline/guardrails.py	
Judge (LLM verifier)	pipeline/judge.py	
Finalizer (templates)	pipeline/finalizer.py	
Persist (execution_records)	pipeline/persist.py	
Active paths in Slice 1: 1 (greetings/templates), 4 (RFQ-grounded operational answers), 8.1–8.5 (safety/escalation). Paths 2/3/5/6/7 are not implemented — they route to safe Path 8 fallbacks rather than producing fabricated answers (per docstring src/app.py:20-23 and src/config/path_registry.py:38-43).

Portfolio (general) mode and RFQ-bound mode: both exist. v1 has dedicated services src/services/portfolio_grounded_reply.py and src/services/rfq_grounded_reply.py. v2 keeps mode as a thread-level field.

Manager connector: src/connectors/manager_ms_connector.py — read-only, supports lookup by both UUID and code (get_rfq_detail, get_rfq_detail_by_code, get_rfq_stages, get_rfq_stages_by_code). Failure mapping covers network, 404, 401, 403, generic non-2xx.

Intelligence connector: NOT IMPLEMENTED. INTELLIGENCE_BASE_URL is declared in settings (src/config/settings.py:31) but no code reads it. The escalation gate has a "intelligence_unreachable" reason code and Path 7 declares "intelligence fields" in registry types (pipeline/escalation_gate.py:117, models/path_registry.py:193) — but those paths are not active.

Memory model:

v1: simple thread + turns persisted (ThreadRow, TurnRow).
v2: bounded working memory (src/models/working_memory.py) — only complete prior pairs, capped by MemoryPolicy.working_pairs from the path registry. Per v2_turn_controller.py:675-701 and models/working_memory.py:20-25: "Batch 10 ONLY captures these entries into state.working_memory. Planner / Compose / Judge prompts are unchanged in Batch 10". The anti-drift test test_batch10_no_history_injection.py enforces this; prompt injection is deferred to a future "Batch 12".
v2 also persists full forensic state to execution_records (src/models/execution_record.py) and reconstructs message history from it (src/datasources/v2_history_datasource.py).
No long-term summarization mechanism is implemented.
Evidence references / citations: evidence is captured via EvidencePackets and target_label (manager-confirmed rfq_code) is returned in V2TurnResponse.target_rfq_code, plus path and reason_code (v2_turn_controller.py:538-573). The user-facing answer text is rendered from manager DTO fields via deterministic renderer or judged compose.

LLM provider/model: Azure OpenAI via src/connectors/llm_connector.py (sync AzureOpenAI SDK). Model = whatever AZURE_OPENAI_CHAT_DEPLOYMENT points to. The repo references "GPT-4o" in comments but no concrete model literal is hardcoded.

Tests (microservices/rfq_copilot_ms/tests/): pytest. Coverage spans pipeline stages (fast_intake, planner, planner_validator, execution_plan_factory, resolver, access, path4 renderer/access/resolver, tool_executor, evidence_check, context_builder, compose, guardrails, judge, finalizer, escalation_gate, persist, working_memory_capture), v2 thread controller, v2 turn smoke tests, models contracts, anti-drift CI guards (no v3 references, no LLM SDK in deterministic stages, fast intake anchoring, structured-output enforcement, registry reader allowlist, no history injection in batch 10), and config sanity. Test totals across the three Python services: 163 test files (find ... -path "*/tests/*" -name "*.py").

Container: Dockerfile only. No docker-compose for copilot. Default DB is SQLite (rfq_copilot.db checked in as chatbot_demo.db is also present).

Known limitations / TODOs (verbatim from code/docs):

v2 app.py docstring: Paths 2/3/5/6/7 not implemented in Slice 1.
v2_turn_controller comments call out: working memory captured only, not yet injected into Planner/Compose/Judge.
Alembic migrations/versions/ is empty; schema bootstrap is Base.metadata.create_all (src/app.py:82-86) marked "DEV ONLY".
Auth: auth_context.py startup log warns "DEV-ONLY auth_context active — single-actor mode reading AUTH_BYPASS_*. Replace with IAM-backed resolver before production." (src/app.py:87-90).
5. Intelligence / parser service status (rfq_intelligence_ms)
Path / framework: microservices/rfq_intelligence_ms, FastAPI, app v0.1.0 (src/app.py:39-43). All routes under /intelligence/v1.
Endpoints
Group	Endpoints	Source
Intelligence (read)	GET /rfqs/{id}/snapshot, /briefing, /workbook-profile, /workbook-review, /artifacts; POST /rfqs/{id}/reprocess/intake, /reprocess/workbook	src/routes/intelligence_routes.py
Manual lifecycle triggers	POST /rfqs/{id}/trigger/intake, /trigger/workbook, /trigger/outcome	src/routes/manual_lifecycle_routes.py
Batch seed runs	GET /batch-seed-runs, GET /batch-seed-runs/{run_id}	src/routes/batch_seed_run_routes.py
Workbook parser (dev)	POST /workbook-parser/parse	src/routes/workbook_parser_routes.py
Health	GET /health	src/routes/health_routes.py
Parsers
Package parser (MR/ZIP) — src/services/package_parser/ with orchestrator, scanners (zip, tree), and extractors (BOM, compliance, identity, RVL, SA-175, section classifier, standards). Cross-checks at package_parser/cross_checks.py.
Workbook parser (Excel) — src/services/workbook_parser/ with orchestrator, readers (workbook_reader, xls_workbook_reader), template matcher, batch seed runner, and extractors (top sheet, BOQ, bid_s, mat breakup, cash flow, general). Cross-checks at workbook_parser/cross_checks.py — implements run_identity_cross_checks, run_numeric_cross_checks, run_cash_flow_cross_checks, run_mat_breakup_cross_checks, run_boq_cross_checks — i.e. anomaly/cross-check flags exist as real code.
Briefing & related services
briefing_service.py — generates intelligence_briefing artifacts. Module docstring: "Current status: partially implemented for the current intake-driven V1 briefing slice" (briefing_service.py:13).
intake_service.py — also marked "partially implemented" (intake_service.py:11-12).
snapshot_service.py, workbook_service.py, review_service.py, analytical_record_service.py, enrichment_service.py, event_processing_service.py, artifact_read_service.py, batch_seed_run_read_service.py are present.
Integration with manager / copilot
Manager → intelligence: no calls found in manager source (grep for INTELLIGENCE_BASE_URL|intelligence_ms|intelligence/v1 in rfq_manager_ms/src returned nothing). Manager publishes lifecycle events to EVENT_BUS_URL; intelligence has lifecycle handlers but they are triggered via manual lifecycle routes / direct handler invocation. Per src/event_handlers/lifecycle_handlers.py:22-26: "Current status: operational for manual-trigger and direct-handler flows; not yet wired to an autonomous event bus consumer."
Intelligence → manager: thin read-only client at src/connectors/manager_connector.py. Uses MANAGER_MS_BASE_URL from compose env.
Copilot → intelligence: not wired. INTELLIGENCE_BASE_URL is declared in copilot settings but never read by code.
Tests
microservices/rfq_intelligence_ms/tests/ contains routes-smoke, intake/briefing/snapshot/workbook flow tests, artifact invariants, batch-seed-run tests, plus package_parser/ (12 files) and workbook_parser/ (17 files) extractor and orchestrator unit tests.

Container
Dockerfile + docker-compose.yml (Postgres + API on port 8001 with alembic upgrade head on startup) + docker-compose.scenario.yml. 4 Alembic migrations applied.

Limitations / TODOs
briefing_service.py and intake_service.py modules carry explicit TODO blocks listing missing pieces (executive summary, document understanding, compliance/risk extraction, evidence/quality tracking, datasource wiring).
lifecycle_handlers.py TODO: "Wire to event bus consumer", "Implement error handling and partial-completion tracking", "Add idempotency checks for duplicate events".
6. Frontend / UI status (rfq_ui_ms)
Path / stack: frontend/rfq_ui_ms. Next.js ^15.5.15 (App Router), React ^18.3.1, TypeScript ^5.4.5, Tailwind 3.4, framer-motion, Radix UI primitives. No DB; no backend.
Pages / routes (App Router under src/app/(dashboard)/)
Path	File
/	src/app/page.tsx
/copilot	src/app/(dashboard)/copilot/page.tsx
/dashboard	src/app/(dashboard)/dashboard/page.tsx
/overview	src/app/(dashboard)/overview/page.tsx
/reminders	src/app/(dashboard)/reminders/page.tsx
/rfqs	src/app/(dashboard)/rfqs/page.tsx
/rfqs/new	src/app/(dashboard)/rfqs/new/page.tsx
/rfqs/[rfqId]	src/app/(dashboard)/rfqs/[rfqId]/page.tsx
Feature components present
RFQ list / portfolio: RFQListScreen.tsx, RFQTable.tsx, RFQCard.tsx, RFQOverviewScreen.tsx.
RFQ detail: RFQDetailScreen.tsx, RfqOperationalWorkspace.tsx, RFQStatusChip.tsx.
Dashboard / KPI cards: DashboardScreen.tsx, ExecutiveDashboardVisuals.tsx, ExecutiveStrategicDetail.tsx, KPICard.tsx, charts (SummaryChart, ExecutivePulseChart, ManagerPipelineChart, EstimatorWorkloadChart).
Stage timeline / lifecycle: RFQStageTimeline.tsx, LifecycleProgressStageBox.tsx.
Intelligence panel: IntelligencePanel.tsx, IntelligenceActionsPanel.tsx, IntelligenceReadinessBar.tsx, PartialIntelligenceState.tsx, ArtifactCard.tsx.
Reminders: ReminderCenterScreen.tsx, ReminderCenterPanel.tsx, ReminderCenterSummaryCard.tsx, ReminderDetailDialog.tsx.
Notes: LeadershipNotesPanel.tsx and a hook use-leadership-notes.ts (no dedicated subtask UI component — see hooks).
Copilot: drawer, page, header, messages, composer, history, history sidebar, floating button, trigger, empty state (src/components/copilot/). The copilot threads connector calls /v2 for turns (connectors/copilot/threads.ts:118-124: "Why /v2 (Slice 1): every turn now goes through FastIntake or the GPT-4o Planner"). Thread management (open/new/list/load) currently calls /v1 per config/api.ts:17-21: "/v1 retains thread management … the v4 architecture's Slice 1 only ships the turn endpoint on /v2." (This is at odds with the backend now shipping /v2/threads/* lifecycle in batch 10 — the cutover commit is on this branch but the frontend apiConfig.copilotApiPath constant still points to /v1 for thread management.)
Copilot mode: Both portfolio (general) and RFQ-bound modes are first-class — CopilotMode is { kind: "general" } or { kind: "rfq_bound", rfqId, rfqLabel } (connectors/copilot/threads.ts:19-31).
Mock vs. real APIs
A toggle exists: NEXT_PUBLIC_USE_MOCK_DATA=true activates demo mode; default reads from real HTTP backends (src/config/api.ts:1).
22 source files reference useMockData (connectors and hooks fall back to demo fixtures when set). Demo data lives in src/demo/manager/ and src/demo/intelligence/.
Default backends: manager http://localhost:8000, intelligence http://localhost:8001, copilot http://localhost:8003 (src/config/api.ts:8-22).
Authentication / login
No login page or auth flow exists. The role is selected client-side and persisted in localStorage (src/context/role-context.tsx:19-38). The frontend forwards a manager auth token from NEXT_PUBLIC_MANAGER_API_TOKEN and relies on the backend's AUTH_BYPASS_ENABLED mode.
Container
No Dockerfile, no docker-compose entry. The frontend runs locally via next dev (scripts/dev.mjs).

Known limitations / TODOs
Frontend has no production build/deploy artifacts in this repo.
Tests are 12 .mjs Node-assertion contract tests at frontend/rfq_ui_ms/tests/, e.g. p0-truth-gates.test.mjs, intelligence-phase-truth.test.mjs, workflow-catalog-truth.test.mjs. They check source-file shape; they do not test the running UI.
7. Cross-service integration
Integration	Status	Evidence
UI → manager	implemented	src/connectors/manager/ (rfqs, stages, workflows, reminders, leadership-notes, base)
UI → copilot	implemented	src/connectors/copilot/threads.ts (turns hit /v2, lifecycle hits /v1)
UI → intelligence	implemented	src/connectors/intelligence/ (artifacts, briefing, snapshot, triggers, workbook)
Copilot → manager	implemented	src/connectors/manager_ms_connector.py — UUID + by-code lookups
Copilot → intelligence	not implemented	INTELLIGENCE_BASE_URL declared in src/config/settings.py:31 but never read by code
Manager → intelligence	indirect / not direct	Manager publishes events to EVENT_BUS_URL (src/connectors/event_bus.py); intelligence has lifecycle handlers but no autonomous event-bus consumer wired (lifecycle_handlers.py:22-26). Triggering happens via manual POST /rfqs/{id}/trigger/... routes.
Intelligence → manager	implemented (read-only)	src/connectors/manager_connector.py
Docker-compose orchestration across services	partial	Per-service compose files exist (microservices/rfq_intelligence_ms/docker-compose.yml, docker-compose.scenario.yml per service); no top-level compose; copilot has none. A scenario stack script exists at scripts/rfqmgmt_scenario_stack.py.
Health checks	implemented	All three services expose /health; intelligence compose has Docker healthcheck (docker-compose.yml:43-48).
Metrics	partial	Manager exposes /metrics Prometheus (src/app.py:189-191). Copilot and intelligence do not.
End-to-end working flow	partial / inferable	Copilot v2 turn → manager lookup → render answer is testable in isolation (smoke tests at tests/smoke/). UI → copilot → manager path 4 has no end-to-end automation in the repo. Intelligence is reachable from the UI but only via manual triggers.
8. Tests and validation evidence
Test framework, Python: pytest with asyncio_mode=auto (microservices/rfq_copilot_ms/pytest.ini). Pytest configs in all three Python services. 163 Python test files across the three services.
Test framework, frontend: Node assert/strict contract scripts (*.test.mjs); 12 files at frontend/rfq_ui_ms/tests/.
Manager tests: 25 unit + 2 integration (tests/unit/, tests/integration/). Coverage: rfq CRUD/lifecycle, stage controller (incl. by-code), subtask, workflow, reminder, file roundtrip, auth bypass + IAM, observability, pagination, atomic code generation, scenario seed.
Copilot tests: pipeline stage tests (16 files in tests/pipeline/), v2 thread/turn smoke tests (12 files in tests/smoke/), datasource tests (3 files), model contract tests (5 files), config tests (2), anti-drift tests (8), docs tests (1), controllers/test_v2_thread_controller.py.
Intelligence tests: routes smoke, intake/briefing/snapshot/workbook flow, artifact invariants, batch-seed-run; package_parser/ 12 files; workbook_parser/ 17 files.
Postman collections: present for manager only at docs/postman/ (rfq_manager_ms_postman_full_walkthrough_v2.json, plus env file). Intelligence has an empty docs/postman/ directory.
CI: only at microservices/rfq_manager_ms/.github/workflows/ci.yml — Python 3.11, runs python scripts/verify.py. No CI for copilot, intelligence, or frontend in this repo.
Areas with no tests: end-to-end UI flow (no Playwright/Cypress); copilot ↔ intelligence (the integration doesn't exist); manager → intelligence event-bus consumer (the consumer doesn't exist).
9. Final implementation status table
Component / capability	Status	Evidence	Safe wording
Manager service core (FastAPI app, ~33 endpoints)	implemented and tested	src/app.py; 27 pytest files; CI workflow	"The service implements …"
Manager: workflow templates from DB seed	implemented and tested	scripts/bootstrap_base_data.py; tests/unit/test_seed_runtime_sync.py	"The service implements …"
Manager: stage progression + mandatory-field gate	implemented and tested	src/utils/rfq_lifecycle.py; rfq_stage_controller.py:579; test_rfq_lifecycle.py, test_rfq_stage_controller.py	"The service implements …"
Manager: blockers as fields on stages (not separate entity)	implemented and tested	src/models/rfq_stage.py:89-90; test_rfq_stage_controller.py	"Blocker handling is modelled as fields on the stage entity rather than as a dedicated table."
Manager: subtasks with soft delete	implemented and tested	src/models/subtask.py:48; test_subtask_controller.py	"The service implements …"
Manager: append-only notes	implemented and tested	src/models/rfq_note.py; test_rfq_stage_controller.py	"The service implements …"
Manager: file upload/list/download/soft-delete	implemented and tested	src/routes/file_route.py; tests/integration/test_fs01_file_roundtrip.py	"The service implements …"
Manager: reminders + reminder rules	implemented, validation pending	src/routes/reminder_route.py; test_reminder_controller_actor_attribution.py, test_reminder_translator.py. POST /reminders/test is documented as "log-only in V1".	"The service implements …, with email delivery presented as a future hardening item."
Manager: stats endpoint (real DB queries)	implemented and tested	src/datasources/rfq_datasource.py:209-277; test_rfq_datasource_analytics.py	"The service implements …"
Manager: analytics (win rate, by-client)	partial	Same datasource: avg_margin_* and estimation_accuracy are returned as None until source data exists (line 318-323)	"The current implementation provides partial support for portfolio analytics: win rate and per-client breakdown are computed from real data, while margin and estimation-accuracy fields are reserved for future sources."
Manager: rfq_history audit table	documented only	docs/KNOWN_LIMITATIONS.md:15; model is declared but dormant	"The architecture specifies a persistent audit table; in V1 the table is intentionally dormant."
Manager: rfq_stage_field_value typed form values	documented only	Same source (line 16); JSON captured_data is the V1 source of truth	"The architecture specifies typed stage-field storage; in V1 form data is stored as JSON on rfq_stage."
Manager: Prometheus /metrics, request IDs	implemented, validation pending	src/app.py:189-191; src/utils/observability.py; test_observability_baseline.py	"The service implements …, with full tracing/export deferred."
Manager: IAM bearer-token auth + bypass	implemented and tested	src/utils/auth.py; test_auth_enforcement.py, test_app_auth_bypass.py	"The service implements …"
Manager: event publication (rfq.created etc.)	partial	src/connectors/event_bus.py; docs/KNOWN_LIMITATIONS.md:14: "intentionally minimal (HTTP best-effort, post-commit) and is not yet a durable outbox/retry architecture"	"The current implementation provides partial event publication via best-effort HTTP, with a durable outbox deferred."
Copilot v1 (legacy lane) thread + turn	implemented, validation pending	src/routes/entry_routes.py, turn_routes.py; tests/smoke/test_v1_preserved.py	"The service implements …, with formal validation presented later."
Copilot v2 thread management (/threads/new, /open, /list, GET /{id})	implemented and tested	src/routes/v2/thread_routes.py; tests/smoke/test_v2_threads_lifecycle.py, test_v2_thread_ownership_enforcement.py, tests/controllers/test_v2_thread_controller.py	"The service implements …"
Copilot v2 turn pipeline (FastIntake, Planner, Validator, Factory, Resolver, Access, ToolExecutor, EvidenceCheck, ContextBuilder, Renderer / Compose, Guardrails, Judge, Finalizer, Persist)	implemented and tested	src/pipeline/; 16 files at tests/pipeline/; smoke tests at tests/smoke/	"The service implements the v4 trust-boundary pipeline …"
Copilot: Path Registry (config + reader allowlist)	implemented and tested	src/config/path_registry.py; tests/anti_drift/test_path_registry_reader_allowlist.py	"The service implements a path registry as the single source of policy truth, with a CI-enforced reader allowlist."
Copilot: EscalationGate / Path 8.x safe failure handling	implemented and tested	src/pipeline/escalation_gate.py; tests/pipeline/test_escalation_gate.py	"The service implements …"
Copilot: Guardrails (deterministic safety floor)	implemented and tested	src/pipeline/guardrails.py; test_guardrails.py; tests/smoke/test_v2_guardrails.py	"The service implements …"
Copilot: LLM Judge	implemented and tested	src/pipeline/judge.py; tests/pipeline/test_judge_path4.py	"The service implements …"
Copilot: Finalizer + templates	implemented and tested	src/pipeline/finalizer.py; test_finalizer.py	"The service implements …"
Copilot: Manager connector (UUID + by-code)	implemented and tested	src/connectors/manager_ms_connector.py; tests/smoke/test_v2_path4_manager_core.py, test_v2_path4_by_code_integration.py	"The service implements …"
Copilot: Intelligence connector	not found / unclear	INTELLIGENCE_BASE_URL declared but unused in rfq_copilot_ms/src/	"No implementation evidence was found for an intelligence connector on the copilot side."
Copilot: Bounded working memory (capture only)	partial	src/models/working_memory.py; tests/pipeline/test_working_memory_capture.py; injection deferred per v2_turn_controller.py:686-690	"The current implementation provides partial support for working memory: complete user-assistant pairs are captured per turn, while injection into Planner/Compose/Judge prompts is deferred."
Copilot: long-term summarization memory	not found / unclear	No summarizer module in src/.	"No implementation evidence was found for long-term summary-based memory."
Copilot: evidence references in answers	implemented and tested	EvidencePacket, target_label propagation, target_rfq_code in V2TurnResponse; test_evidence_check_path4.py.	"The service implements …"
Copilot: portfolio/general mode	implemented, validation pending	src/services/portfolio_grounded_reply.py; v1 path. v2 carries mode through threads.	"The service implements …"
Copilot: RFQ-bound mode	implemented and tested	Same files; Path 4 in v2 is RFQ-bound; smoke and pipeline tests	"The service implements …"
Copilot: Paths 2/3/5/6/7	deferred/future	src/app.py:20-23; src/config/path_registry.py:38-43	"These capabilities are deferred to future work; the current pipeline routes such requests to safe fallback templates."
Copilot: Alembic migrations	documented only	migrations/versions/ is empty; schema bootstrap via Base.metadata.create_all (src/app.py:82-86)	"The service uses an in-place schema bootstrap; Alembic migrations are reserved for a future hardening step."
Intelligence: REST endpoints (snapshot, briefing, workbook-profile, workbook-review, artifacts, reprocess, manual-trigger, batch-seed-runs, workbook-parser/parse, health)	implemented, validation pending	src/routes/; tests/test_routes_smoke.py, tests/test_health.py, tests/test_batch_seed_run_read_routes.py	"The service implements …"
Intelligence: MR-package parser (zip/tree scanners; BOM, compliance, identity, RVL, SA-175, standards, section classifier extractors; cross checks)	implemented and tested	src/services/package_parser/; 12 tests at tests/package_parser/	"The service implements …"
Intelligence: Workbook (Excel) parser (top sheet, BOQ, bid_s, mat breakup, cash flow, general extractors; readers; template matcher; cross checks)	implemented and tested	src/services/workbook_parser/; 17 tests at tests/workbook_parser/	"The service implements …"
Intelligence: anomaly / cross-check flags	implemented and tested	src/services/workbook_parser/cross_checks.py; tests/workbook_parser/test_cross_checks.py, tests/package_parser/test_cross_checks.py	"The service implements …"
Intelligence: briefing generation	partial	src/services/briefing_service.py:13 ("partially implemented for the current intake-driven V1 briefing slice"); tests/test_briefing_service.py	"The current implementation provides partial support for intelligence-briefing generation, focused on intake-driven content with truthful fallbacks."
Intelligence: intake parsing pipeline	partial	src/services/intake_service.py:11-12; tests/test_intake_service.py	"The current implementation provides partial support for intake parsing."
Intelligence: event-bus consumer for manager events	not found / unclear	event_handlers/lifecycle_handlers.py:22-26 "operational for manual-trigger and direct-handler flows; not yet wired to an autonomous event bus consumer".	"No implementation evidence was found for an autonomous event-bus consumer; lifecycle cascades currently run via direct handler invocation or the /trigger/... routes."
Intelligence integration with copilot	not found / unclear	No copilot code path reads INTELLIGENCE_BASE_URL.	"No implementation evidence was found for a copilot–intelligence integration."
Intelligence integration with manager (read-only)	implemented	src/connectors/manager_connector.py	"The service implements a read-only connector to the manager service."
Frontend: pages (overview, dashboard, RFQ list, RFQ detail, RFQ create, reminders, copilot)	implemented, validation pending	src/app/(dashboard)/; 12 contract test scripts at tests/	"The frontend implements …, with end-to-end UI validation deferred."
Frontend: real-vs-mock data toggle	implemented	src/config/api.ts:1; 22 source files reference useMockData; demo fixtures at src/demo/	"The frontend supports both live API consumption and a demonstration mode driven by local fixtures."
Frontend: copilot panel (portfolio + RFQ-bound modes)	implemented	src/components/copilot/; src/connectors/copilot/threads.ts (turns hit /v2, lifecycle /v1)	"The frontend implements …"
Frontend: authentication / login	not found / unclear	No login page. Role is selected client-side and stored in localStorage (src/context/role-context.tsx)	"No implementation evidence was found for an end-user authentication flow; the platform relies on the manager service's auth layer and a forwarded bearer token."
Frontend: end-to-end UI tests (Playwright/Cypress)	not found / unclear	None in repo (only Node assert contract scripts)	"No implementation evidence was found for end-to-end UI test automation."
Cross-service Docker Compose orchestration	partial	Per-service compose only; copilot has no compose; no top-level compose. Scenario script at scripts/rfqmgmt_scenario_stack.py.	"The current implementation provides per-service container definitions with a scenario orchestration script; a unified compose stack is not yet provided."
CI / GitHub Actions	partial	Single workflow at microservices/rfq_manager_ms/.github/workflows/ci.yml	"Continuous integration is configured for the manager service only; CI for the copilot, intelligence, and frontend codebases is deferred."
10. Final warnings — claims to avoid
Do not write any of the following in the report; the code does not support them:

"The copilot service is integrated with the intelligence service." — INTELLIGENCE_BASE_URL is declared but unused in rfq_copilot_ms/src/.
"The manager service automatically triggers intelligence parsing through an event bus." — lifecycle_handlers.py itself states cascades run via manual-trigger / direct-handler flows; the autonomous consumer is not wired.
"The copilot pipeline supports Paths 2, 3, 5, 6, or 7" — explicitly documented as not implemented in Slice 1.
"Working memory is injected into Planner / Compose / Judge prompts." — explicitly captured-only; injection is deferred.
"Long-term summarization / persistent semantic memory is implemented." — no such module exists.
"RFQ history (audit table) is persisted." — rfq_history model is declared but dormant per KNOWN_LIMITATIONS.md.
"Margin / estimation accuracy / by-client average margin analytics are computed from data." — these fields are returned as None (rfq_datasource.py:318-323).
"The reminder system sends real emails." — the test endpoint is documented as "log-only in V1".
"The platform has end-user authentication / SSO / login." — no login UI; role is local; backends run with bypass mode by default in dev.
"RFQ code generation is concurrency-safe." — RELEASE_v1.0.0.md:21 flags "LG-06: RFQ code generation is still non-atomic under high concurrency."
"The whole platform is deployed via a single docker-compose." — per-service compose only; copilot has none.
"Tests cover the end-to-end UI flow." — frontend tests are 12 Node assert contract scripts, not browser-driven E2E.
"Copilot uses Alembic migrations." — migrations/versions/ is empty; bootstrap is create_all.
"The copilot LLM is GPT-4o specifically." — the deployment string is configurable; only comments name GPT-4o.
"CI runs on every service." — only the manager has a workflow file.
"Blockers are a separate entity / table." — they are columns on rfq_stage