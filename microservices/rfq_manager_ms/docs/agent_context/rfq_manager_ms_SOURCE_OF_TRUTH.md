# rfq_manager_ms — Source of Truth for AI Agents

## 1. Purpose of This Document

This document is the canonical technical context for future AI coding agents working on `rfq_manager_ms`. It is based on the implementation inspected in `src/`, migrations, tests, scripts, runtime configuration, OpenAPI files, and existing docs. When this document conflicts with code, inspect code first and update this document after changing behavior.

## 2. Service Summary

`rfq_manager_ms` is a FastAPI service that owns operational RFQ lifecycle truth: RFQ records, workflow templates, workflow-driven stage instances, stage progression, stage notes, stage files, subtasks, reminders, reminder rules, RFQ stats, analytics, exports, health, metrics, auth enforcement seams, and lifecycle event publication seams.

## 3. Business Role

The service is the operational lifecycle backbone of the RFQ platform. It is not just CRUD: creating an RFQ selects a workflow, instantiates stage rows from workflow stage templates, sets the active stage, calculates planned dates from the deadline, allocates a human-readable RFQ code, and then protects stage progression through blocker, mandatory-field, subtask, team, and terminal-outcome rules. It provides the read/write surfaces used by the UI and by adjacent services that need operational RFQ state.

## 4. Ownership Boundary

### 4.1 What rfq_manager_ms Owns

- Core RFQ metadata: name, client, industry, country, priority, owner, deadline, description, status, progress, outcome reason.
- Atomic RFQ code allocation through `rfq_code_counter`.
- Workflow templates in `workflow` and stage templates in `stage_template`.
- Customizable workflow selection through `workflow.selection_mode`, `workflow.base_workflow_id`, `stage_template.is_required`, `skip_stages`, and `stage_overrides`.
- RFQ stage instances in `rfq_stage`, including current stage tracking, planned/actual dates, blocker state, captured stage data, mandatory field snapshots, and stage progress.
- Stage lifecycle progression and terminal RFQ outcomes.
- Stage notes in `rfq_note`.
- Stage files in `rfq_file`, local file storage, download, and soft delete.
- Subtasks in `subtask`, including soft delete and parent-stage progress rollup.
- Manual and automatic reminders in `reminder`.
- Reminder automation rules in `reminder_rule`.
- Dashboard stats, analytics, CSV export, health, request IDs, and Prometheus-style metrics.
- Auth/permission enforcement at API boundaries, with IAM connector or explicit local bypass.
- Best-effort lifecycle event publication to an HTTP event bus seam.
- Scenario seed data and local scenario-stack operational fixtures.

### 4.2 What rfq_manager_ms Does Not Own

- Chatbot reasoning.
- LLM response generation.
- Document intelligence.
- Workbook parsing.
- MR/package parsing.
- AI prediction or historical learning.
- Frontend UI behavior.
- Estimator judgment or bid/no-bid business judgment beyond enforcing recorded lifecycle decisions.
- Durable event outbox/retry infrastructure.
- Full tracing/export observability stack.
- Production secret management or production orchestration.
- Direct ownership of `rfq_intelligence_ms` artifacts, except exposing simple file-derived intelligence milestone booleans in RFQ detail/list responses.

### 4.3 Partial Seams / Stubs

- IAM: active seam via `IAM_SERVICE_URL`; bearer token is resolved by `GET {IAM_SERVICE_URL}/auth/resolve` when `AUTH_BYPASS_ENABLED=false`.
- Auth bypass: explicit local/dev bypass injects a demo actor and permissions.
- Event bus: active best-effort HTTP seam via `EVENT_BUS_URL`; publish failures are logged and do not roll back committed DB writes.
- Reminder delivery: `NotificationService` logs reminder sends; no real email/SMS provider is active.
- Metrics: active minimal Prometheus endpoint at `GET /metrics`; no OpenTelemetry pipeline.
- Audit/history: `rfq_history` table exists but is intentionally dormant in V1.
- Normalized stage fields: `rfq_stage_field_value` exists but is intentionally dormant in V1; active source of truth is `rfq_stage.captured_data`.
- `JWT_SECRET`: configured but currently reserved; it is not used as standalone JWT validation.
- `.env.example` mentions `AZURE_BLOB_CONNECTION_STRING`, but implementation uses local filesystem helpers only.

## 5. Current Implementation Snapshot

| Item | Current implementation |
|---|---|
| framework | FastAPI 0.115.0 |
| runtime/language | Python 3.11+, synchronous SQLAlchemy app |
| database | PostgreSQL 16 target; tests use SQLite |
| API prefix | Business endpoints under `/rfq-manager/v1`; operational endpoints `/health`, `/metrics`, and FastAPI `/docs` are outside the prefix |
| resource families | RFQ, Workflow, RFQ Stage, Subtask, File, Reminder, Health, Metrics |
| number of endpoints if confirmable | 32 business route handlers in code plus `/health` and `/metrics`; current OpenAPI YAML lists fewer and is stale |
| main tables | `rfq`, `rfq_code_counter`, `workflow`, `stage_template`, `rfq_stage`, `subtask`, `rfq_note`, `rfq_file`, `reminder`, `reminder_rule`, dormant `rfq_history`, dormant `rfq_stage_field_value` |
| migrations status | Alembic with baseline plus branch/merge migrations through `7c1a9d2b4e6f`; `env.py` omits `rfq_code_counter` import |
| test status | `PYTHONIOENCODING=utf-8 python scripts/verify.py` passed: ruff, 240 tests, startup sanity; 107 warnings |
| Docker status | `Dockerfile` builds API; `docker-compose.scenario.yml` runs Postgres, API, and mock event bus |
| CI status if visible | `.github/workflows/ci.yml` runs Python 3.11 and `python scripts/verify.py` on push/PR to `main` |
| implementation maturity | V1 operational baseline with strong lifecycle tests; event, audit, delivery, and observability remain intentionally minimal |

## 6. Repository Structure

Actual service structure inspected:

```text
rfq_manager_ms/
  .env.example
  .github/workflows/ci.yml
  Dockerfile
  README.md
  RELEASE_v1.0.0.md
  alembic.ini
  docker-compose.scenario.yml
  migrations/
  mock_event_bus.py
  pytest.ini
  requirements.txt
  requirements-dev.txt
  scripts/
  src/
  tests/
  docs/
  uploads_scenario/
```

Important roles:

| Path | Role |
|---|---|
| `src/app.py` | FastAPI app factory, middleware, error handlers, health/metrics, route registration |
| `src/app_context.py` | Dependency wiring/composition root for DB sessions, datasources, connectors, controllers |
| `src/database.py` | SQLAlchemy engine, `SessionLocal`, declarative `Base`, `get_db()` |
| `src/config/settings.py` | Environment-driven settings with fail-fast `DATABASE_URL` validation |
| `src/routes/` | HTTP endpoints only; parse requests and call controllers |
| `src/controllers/` | Business logic, orchestration, validation, lifecycle rules, transaction commits |
| `src/datasources/` | ORM query and persistence helpers |
| `src/models/` | SQLAlchemy ORM models |
| `src/translators/` | Pydantic request/response schemas plus mapping/normalization helpers |
| `src/connectors/` | IAM and event bus external seams |
| `src/services/` | `NotificationService` for reminder batch/reconciliation behavior |
| `src/utils/` | Auth, errors, pagination, file path safety, RFQ status/lifecycle helpers, observability |
| `migrations/` | Alembic migration chain |
| `tests/unit/` | Controller, datasource, auth, reminder, lifecycle, seed, observability, connector tests |
| `tests/integration/` | API layer and file-storage roundtrip tests |
| `scripts/bootstrap_base_data.py` | Seeds base workflows and reminder rules |
| `scripts/seed_rfqmgmt_scenarios.py` | Seeds deterministic scenario RFQs and manifest |
| `scripts/verify.py` | Authoritative quality gate: ruff, pytest, startup sanity |
| `docs/rfq_manager_ms_openapi_current.yaml` | Existing contract file, currently missing newer code endpoints |
| `docs/archive/` | Historical docs/UI proposals; do not treat as implementation truth |

## 7. BACAB Architecture Mapping

| Layer | Responsibility | Actual examples | Future agents must not do |
|---|---|---|---|
| `routes/` | Expose HTTP endpoints, parse parameters/body/files, enforce auth dependency, call controllers, return response objects | `rfq_route.create_rfq`, `rfq_stage_route.advance_stage`, `file_route.download_file` | Do not query DB, compute lifecycle transitions, write files directly, or bypass controllers |
| `controllers/` | Own business rules, orchestration, validation, commits, cross-resource workflows | `RfqController.create/update/cancel`, `RfqStageController.advance/update`, `ReminderController.create/process_reminders` | Do not format HTTP responses or hide raw SQL here unless there is no datasource alternative |
| `datasources/` | Own DB query/insert/update/filter/sort/pagination primitives | `RfqDatasource.list/get_next_code`, `RfqStageDatasource.add_note`, `FileDatasource.soft_delete` | Do not make lifecycle decisions or know HTTP/auth semantics |
| `models/` | Define ORM tables and persisted fields | `RFQ`, `Workflow`, `StageTemplate`, `RFQStage`, `ReminderRule` | Do not call datasources/controllers or orchestrate workflows |
| `translators/` | Define API DTOs and map/normalize internal objects to response shapes | `RfqCreateRequest`, `RfqStageUpdateRequest`, `to_detail`, `file_to_schema` | Do not add persistence, external calls, or controller orchestration |
| `connectors/` | Isolate external systems/seams | `IAMServiceConnector`, `EventBusConnector` | Do not contain RFQ lifecycle rules |
| `services/` | Internal reusable/batch behavior already used by repo | `NotificationService` reconciles/generates/processes automatic reminders | Do not turn services into a hidden manager layer for unrelated business domains |
| `utils/` | Shared helpers only | `rfq_lifecycle`, `rfq_status`, `file_storage`, `observability`, `pagination`, `errors`, `auth` | Do not grow hidden workflow orchestration here |
| `config/` | Runtime settings | `Settings`, `build_settings` | Do not read random env vars throughout the app |
| `app_context.py` | Dependency wiring/composition root | Creates datasources, connectors, controllers with shared request DB session | Do not put business rules here |
| `app.py` | FastAPI entry point | CORS, request ID/metrics middleware, exception handlers, `/health`, `/metrics`, route inclusion | Do not implement endpoint business logic here |

Golden request flow:

```text
HTTP request
-> route
-> controller
-> datasource/connector/service
-> model/database/external seam
-> translator/response
```

Forbidden patterns:

- Route directly querying database.
- Route owning lifecycle decisions.
- Datasource making business lifecycle decisions.
- Model calling datasource.
- Utils becoming an orchestration layer.
- Manager service owning chatbot/intelligence behavior.

## 8. Dependency Wiring and App Startup

`src.app:app` is created by `create_app()`. The factory:

- Creates `FastAPI(title="rfq_manager_ms", version="1.0.0")`.
- Configures request ID logging.
- Adds CORS middleware from comma-separated `settings.CORS_ORIGINS`.
- Adds HTTP middleware that resolves/preserves `X-Request-ID` or `X-Correlation-ID`, records metrics, logs request completion, and returns `X-Request-ID`.
- Logs auth mode at startup with `@app.on_event("startup")`.
- Converts `AppError`, `RequestValidationError`, and unhandled exceptions to JSON with `request_id`.
- Defines `GET /health` returning `{"status":"ok"}`.
- Defines `GET /metrics` returning Prometheus text from `prometheus_client`.
- Registers all business routers under `/rfq-manager/v1`.

`src.database` builds a sync SQLAlchemy engine from `settings.DATABASE_URL`. `get_db()` yields a session per request and closes it; controllers explicitly commit.

`src.app_context` wires:

- One SQLAlchemy `Session` into datasources.
- `IAMServiceConnector` from `IAM_SERVICE_URL`.
- `EventBusConnector` from `EVENT_BUS_URL`.
- Controllers with required datasources/connectors and the same DB session.

## 9. Domain Model and Database

### ORM Models

| Model | Table | Important fields and relationships |
|---|---|---|
| `RFQ` | `rfq` | UUID `id`; required `name`, `client`, `deadline`, `owner`, `workflow_id`, `priority`; `rfq_code` unique nullable; `status`, `progress`, nullable `current_stage_id`, nullable `outcome_reason`; indexed client/deadline/owner/priority/status/current_stage/created_at |
| `RFQCodeCounter` | `rfq_code_counter` | `prefix` PK, `last_value`; used for atomic RFQ code allocation |
| `Workflow` | `workflow` | UUID `id`; `name`, unique `code`, `description`, `is_active`, `is_default`, `selection_mode`, nullable `base_workflow_id`; relationship `stages`; self relationship `base_workflow` |
| `StageTemplate` | `stage_template` | Belongs to workflow; `name`, `order`, `default_team`, `planned_duration_days`, nullable `mandatory_fields`, `is_required` |
| `RFQStage` | `rfq_stage` | Belongs to RFQ; optional `stage_template_id`; `name`, `order`, `assigned_team`, `status`, `progress`, planned/actual dates, `blocker_status`, `blocker_reason_code`, JSON `captured_data`, `mandatory_fields` |
| `Subtask` | `subtask` | Belongs to stage; `name`, `assigned_to`, `due_date`, `progress`, `status`, `deleted_at` soft delete |
| `RFQNote` | `rfq_note` | Belongs to stage; append-only `user_name`, `text`, `created_at` |
| `RFQFile` | `rfq_file` | Belongs to stage; original `filename`, stored `file_path`, `type`, `uploaded_by`, `size_bytes`, `uploaded_at`, `deleted_at` soft delete |
| `Reminder` | `reminder` | Belongs to RFQ and optionally stage/rule; `type`, `message`, `due_date`, `assigned_to`, `status`, `source`, `created_by`, `send_count`, `last_sent_at`, `updated_at` |
| `ReminderRule` | `reminder_rule` | `name`, `description`, `scope`, `is_active`, `created_at` |
| `RFQHistory` | `rfq_history` | Dormant audit table; no active controller/service writes |
| `RFQStageFieldValue` | `rfq_stage_field_value` | Dormant normalized stage field table; no active controller/service writes |

### Important Schemas and Enums

- `RfqCreateRequest`: `name`, `client`, `deadline`, `owner`, `workflow_id`, `industry`, `country`, `priority`, optional `description`, `code_prefix`, `stage_overrides`, `skip_stages`.
- `RfqUpdateRequest`: metadata only; extra fields are forbidden, so `status` cannot be patched.
- `RfqCancelRequest`: explicit cancellation reason.
- `RfqStageUpdateRequest`: `captured_data`, `blocker_status`, `blocker_reason_code`; manual `progress` is rejected.
- `RfqStageAdvanceRequest`: `confirm_no_go_cancel`, `terminal_outcome`, `lost_reason_code`, `outcome_reason`.
- `ReminderCreateRequest`: RFQ/stage link, type, message, due date, assignee.
- RFQ statuses: `In preparation`, `Awarded`, `Lost`, `Cancelled`.
- Terminal RFQ statuses: `Awarded`, `Lost`, `Cancelled`.
- Reminder statuses: response normalizes to `open`, `overdue`, `resolved`.
- Reminder sources: `manual`, `automatic`.

### ERD-Style Textual Summary

```text
workflow 1 -> many stage_template
workflow 1 -> many derived workflow via base_workflow_id
workflow 1 -> many rfq
rfq 1 -> many rfq_stage
rfq current_stage_id -> rfq_stage.id nullable
stage_template 1 -> many rfq_stage via stage_template_id nullable for legacy rows
rfq_stage 1 -> many subtask
rfq_stage 1 -> many rfq_note
rfq_stage 1 -> many rfq_file
rfq 1 -> many reminder
rfq_stage 1 -> many reminder nullable
reminder_rule 1 -> many reminder nullable
rfq 1 -> many rfq_history dormant
rfq_stage 1 -> many rfq_stage_field_value dormant
```

### Migration Chain

```text
phase2_filter_indexes (legacy no-op root)
-> bc8fe52aaace authoritative schema baseline
-> 4b1f8f1d4a5b add rfq_stage.stage_template_id
-> 9f3c7e21b6ad add reminder.updated_at
-> branch A: e2b7d4f5a1c2 add reminder.source/reminder_rule_id
-> branch B: 2d98d9a8b8a4 add rfq_code_counter
-> 5f3a1b8c9d0e merge reminder and rfq code heads
-> 7c1a9d2b4e6f add workflow customization metadata
```

Risk: `migrations/env.py` imports most model modules but not `src.models.rfq_code_counter`; future Alembic autogenerate may miss the counter table unless fixed.

## 10. API Surface

Auth dependencies are present on every business endpoint. `/health` and `/metrics` are public.

### Health

| Method | Path | Route file | Controller | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/health` | `src/app.py` | none | Liveness | none | `{status:"ok"}` | metrics/logging only | none | observability/auth tests |

### RFQ

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/rfq-manager/v1/rfqs` | `rfq_route.py` | `RfqController.create` | Create RFQ and stages | RFQ metadata, workflow_id, code_prefix, optional stage_overrides/skip_stages | `RfqDetail` | inserts RFQ/stages, allocates rfq_code, commits, publishes `rfq.created` | `rfq:create` | unit/integration |
| GET | `/rfq-manager/v1/rfqs` | `rfq_route.py` | `list` | List/search/filter/sort/paginate | search, status list, priority, owner, created_after/before, sort, page, size | paginated `RfqSummary` | read only | `rfq:read` | unit/integration |
| GET | `/rfq-manager/v1/rfqs/export` | `rfq_route.py` | `export_csv` | CSV export | same filters except pagination | `text/csv` attachment | read only | `rfq:export` | unit/integration |
| GET | `/rfq-manager/v1/rfqs/stats` | `rfq_route.py` | `get_stats` | KPI stats | none | totals/open/critical/avg_cycle | read only | `rfq:stats` | datasource tests |
| GET | `/rfq-manager/v1/rfqs/analytics` | `rfq_route.py` | `get_analytics` | Analytics | none | margins null, win_rate, by_client | read only | `rfq:analytics` | datasource tests |
| GET | `/rfq-manager/v1/rfqs/{rfq_id}` | `rfq_route.py` | `get` | RFQ detail | UUID | `RfqDetail` plus file-derived intelligence flags | read only | `rfq:read` | integration |
| PATCH | `/rfq-manager/v1/rfqs/{rfq_id}` | `rfq_route.py` | `update` | Metadata/deadline update | metadata fields only | `RfqDetail` | updates RFQ, may recalc stage dates, may publish `rfq.deadline_changed` | `rfq:update` | unit/integration |
| POST | `/rfq-manager/v1/rfqs/{rfq_id}/cancel` | `rfq_route.py` | `cancel` | Explicit safe cancel | outcome_reason | terminal `RfqDetail` | freezes stages, clears current stage, may publish `rfq.status_changed` | `rfq:update` | unit/integration |

### Workflow

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/rfq-manager/v1/workflows` | `workflow_route.py` | `list` | List workflows | none | workflow summaries with effective stage_count | read only | `workflow:read` | unit |
| GET | `/rfq-manager/v1/workflows/{workflow_id}` | `workflow_route.py` | `get` | Detail with stage templates | UUID | `WorkflowDetail` | read only | `workflow:read` | unit |
| PATCH | `/rfq-manager/v1/workflows/{workflow_id}` | `workflow_route.py` | `update` | Update workflow metadata | name, description, is_active, is_default | `WorkflowDetail` | may clear previous default | `workflow:update` | unit |

### RFQ Stage

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/rfq-manager/v1/rfqs/{rfq_id}/stages` | `rfq_stage_route.py` | `list` | Ordered stages | RFQ UUID | stage list | read only | `rfq_stage:read` | unit |
| GET | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}` | `rfq_stage_route.py` | `get` | Stage detail | RFQ/stage UUIDs | stage plus notes/files/subtasks | read only | `rfq_stage:read` | unit |
| PATCH | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}` | `rfq_stage_route.py` | `update` | Captured data/blocker update | captured_data, blocker fields | stage detail | updates blocker/history-in-captured-data | `rfq_stage:update` | unit/integration |
| POST | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/notes` | `rfq_stage_route.py` | `add_note` | Add note | text | note | inserts note | `rfq_stage:add_note` | unit |
| POST | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/files` | `rfq_stage_route.py` | `upload_file` | Upload file | multipart file, form `type` | file response with download_url | writes disk file, inserts file row | `rfq_stage:add_file` | unit/integration |
| POST | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/advance` | `rfq_stage_route.py` | `advance` | Advance current stage | optional no-go/terminal body | stage detail | updates stages/RFQ, commits, publishes events | `rfq_stage:advance` and team rule | extensive unit/integration |

### Subtask

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/subtasks` | `subtask_route.py` | `create` | Create subtask | name, assigned_to, due_date | subtask | inserts subtask, recalculates stage progress | `subtask:create` | unit |
| GET | same | `subtask_route.py` | `list` | Active subtasks | RFQ/stage UUIDs | list | read only | `subtask:read` | unit |
| PATCH | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/subtasks/{subtask_id}` | `subtask_route.py` | `update` | Update subtask | metadata/progress/status | subtask | updates subtask, recalculates stage progress | `subtask:update` | unit |
| DELETE | same | `subtask_route.py` | `delete` | Soft delete | UUIDs | 204 | sets `deleted_at`, recalculates stage progress | `subtask:delete` | unit |

### File

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/rfq-manager/v1/rfqs/{rfq_id}/stages/{stage_id}/files` | `file_route.py` | `list_for_stage` | List active stage files | UUIDs | file list | read only | `file:list` | integration |
| GET | `/rfq-manager/v1/files/{file_id}/download` | `file_route.py` | `get_file_path` | Download local file | file UUID | file stream | read disk | `file:download` | integration |
| DELETE | `/rfq-manager/v1/files/{file_id}` | `file_route.py` | `delete` | Soft delete file | file UUID | 204 | sets `deleted_at`; physical file remains | `file:delete` plus team/override rule | unit/integration |

### Reminder

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Auth | Tests |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/rfq-manager/v1/reminders` | `reminder_route.py` | `create` | Create manual reminder | rfq_id, optional rfq_stage_id, type, message, due_date, assigned_to | reminder | inserts manual reminder | `reminder:create` | unit/integration |
| GET | `/rfq-manager/v1/reminders` | `reminder_route.py` | `list` | List/filter reminders | user, status, rfq_id | list | read only | `reminder:read` | unit |
| GET | `/rfq-manager/v1/reminders/stats` | `reminder_route.py` | `get_stats` | Reminder KPIs | none | open/overdue/due_week/active RFQs | read only | unit |
| GET | `/rfq-manager/v1/reminders/rules` | `reminder_route.py` | `list_rules` | List automation rules | none | rules | read only | `reminder:read` | unit |
| PATCH | `/rfq-manager/v1/reminders/rules/{rule_id}` | `reminder_route.py` | `update_rule` | Toggle rule | is_active | rule | updates rule | `reminder:update_rules` | unit |
| POST | `/rfq-manager/v1/reminders/test` | `reminder_route.py` | `test_email` | Log-only test send | none | message | log only | `reminder:test` | unit |
| POST | `/rfq-manager/v1/reminders/process` | `reminder_route.py` | `process_reminders` | Process due reminders | none | batch result | reconciles automatic reminders, updates send fields/status | `reminder:process` | unit |
| POST | `/rfq-manager/v1/reminders/{reminder_id}/resolve` | `reminder_route.py` | `resolve` | Resolve manual reminder | UUID | reminder | sets status resolved | `reminder:update` | unit/integration |

### Stats / Analytics / Export

These are RFQ endpoints: `GET /rfqs/stats`, `GET /rfqs/analytics`, `GET /rfqs/export`. Stats and analytics are implemented in `RfqDatasource`; export formatting is in `RfqController.export_csv`.

### Metrics

| Method | Path | Route file | Controller | Purpose | Key response shape | Auth | Tests |
|---|---|---|---|---|---|---|
| GET | `/metrics` | `src/app.py` | none | Prometheus-style HTTP metrics | text exposition including `rfq_manager_http_requests_total` and duration histogram | none | observability tests |

## 11. Core Workflows

### 11.1 Create RFQ

```text
POST /rfq-manager/v1/rfqs
-> rfq_route.create_rfq
-> RfqController.create
-> WorkflowDatasource.get_by_id
-> RfqDatasource.get_next_code
-> RfqDatasource.create
-> RfqStageDatasource.create for each active template
-> DB commit
-> EventBusConnector.publish("rfq.created") best-effort
-> rfq_translator.to_detail
```

Implementation details:

- Validates workflow exists.
- Resolves effective stage templates. Fixed workflows use their own stages; customizable workflows use their base workflow stages.
- Applies `skip_stages` only for customizable workflows.
- Rejects zero-stage RFQ creation.
- Rejects skipping required stage templates.
- Validates deadline can fit selected stage durations from today.
- Allocates `rfq_code` atomically with prefix `IF` or `IB`.
- Creates RFQ with status `In preparation`.
- Back-calculates stage planned dates from deadline.
- Creates `rfq_stage` rows in sequential order after skip filtering.
- Copies `stage_template_id`, name, default or overridden team, mandatory fields, planned dates.
- First stage is `In Progress` and gets `actual_start=date.today()`.
- Sets `rfq.current_stage_id` to first stage.
- Publishes `rfq.created` after commit, best-effort.

### 11.2 List/Search/Filter RFQs

`RfqDatasource.list` filters by statuses, priority, owner, created date range, and search over name/client. If no status is supplied, it filters to `RFQ_OPERATIONAL_STATUSES`. Sorting is whitelist-only: `name`, `client`, `deadline`, `created_at`, `priority`, `status`, `progress`, `owner`; `-field` means descending. Pagination is page/size, size capped at 100.

### 11.3 Get RFQ Detail

`RfqController.get` fetches by ID and returns `RfqDetail`. It enriches `current_stage_name`, `workflow_name`, and file-derived intelligence milestones:

- `source_package_available`/`source_package_updated_at` from active stage files of type `Client RFQ`.
- `workbook_available`/`workbook_updated_at` from active stage files of type `Estimation Workbook`.

It does not parse documents or own intelligence artifacts.

### 11.4 Update RFQ

`PATCH /rfqs/{id}` is metadata/deadline update only. `RfqUpdateRequest` forbids extra fields, so `status` cannot be patched. Terminal RFQs reject standard update attempts. If `deadline` changes, stage planned dates are recalculated for non-completed/non-skipped stages. `outcome_reason` can only be set when the RFQ is already terminal. Deadline changes publish `rfq.deadline_changed` after commit.

Lifecycle status change uses explicit cancel or final stage advancement, not generic PATCH.

### 11.5 Workflow Listing and Detail

Workflow list/detail returns active and inactive workflows. For customizable workflows, response stages are resolved from the base workflow catalog. Updating `is_default=true` clears previous defaults before setting the new one.

### 11.6 Stage Update

Stage update accepts `captured_data`, `blocker_status`, and `blocker_reason_code`. Manual `progress` is rejected because stage progress is derived from subtasks/lifecycle. Captured data is normalized for controlled fields: go/no-go, design/BOQ yes-no decisions, estimation/final price amounts/currencies, approval signatures, terminal outcome fields, and lifecycle history events. Negative design/BOQ decisions auto-block the stage and require a blocker reason.

### 11.7 Stage Advance

Stage advance flow:

```text
POST /rfqs/{rfq_id}/stages/{stage_id}/advance
-> route passes auth actor/team/permissions
-> RfqStageController.advance
-> validate stage exists and belongs to RFQ
-> validate actor team or cross-team permission
-> validate stage is rfq.current_stage_id
-> reject blockers
-> validate mandatory fields
-> reject incomplete active subtasks
-> handle no-go cancellation if needed
-> handle terminal Awarded/Lost if this is last stage
-> complete current stage
-> start next stage and update current_stage_id, or complete terminal state
-> recalculate RFQ progress
-> commit
-> publish events best-effort
```

Rules implemented:

- Only the current active stage can advance.
- Actor team must match `stage.assigned_team` unless permissions include `*`, `rfq_stage:*`, or `rfq_stage:advance`.
- `blocker_status=="Blocked"` returns conflict and does not mutate state.
- Missing mandatory fields return 422.
- Active subtasks must all be `Done` with `progress==100`.
- Go/No-Go `no_go` requires `confirm_no_go_cancel=true` and `outcome_reason`; it cancels RFQ, freezes current/future stages as skipped, clears current stage, and publishes `rfq.status_changed`.
- Last stage requires terminal outcome Awarded or Lost. Lost requires a reason code, and `other` requires detail in captured data.
- Normal non-terminal advance sets current stage `Completed`, `progress=100`, `actual_end=today`; next stage becomes `In Progress`, gets `actual_start=today`, and becomes `rfq.current_stage_id`.
- If no next stage, the RFQ is not silently auto-awarded/lost; explicit terminal outcome is required.
- `stage.advanced` is published after successful commit. Terminal outcome also publishes `rfq.status_changed`.

### 11.8 Stage Notes

`POST /stages/{stage_id}/notes` validates the stage belongs to the RFQ and inserts an append-only `rfq_note` row with authenticated `user_name` and request text. Stage detail embeds notes ordered newest first.

### 11.9 Stage Files

Upload is multipart through the stage route. The controller:

- Validates stage ownership.
- Enforces `MAX_FILE_SIZE_MB`.
- Resolves `FILE_STORAGE_PATH`.
- Writes under `<storage_root>/<rfq_id>/<stage_id>/<file_id>_<sanitized_filename>`.
- Stores a relative POSIX path in `rfq_file.file_path`.
- Returns a response with `download_url` and `storage_reference`; it does not expose raw `file_path`.

List/download/delete are in `file_route.py`. Download resolves paths under the storage root and supports legacy `uploads/` prefix. Delete is a soft delete (`deleted_at`) and physical files remain on disk. Delete requires actor team to match the stage assigned team unless broad file/RFQ permissions allow override.

### 11.10 Subtasks

Subtasks belong to stages. Create requires nonblank name, assignee, and due date. Due date must fall within the stage window; if actual start exists, the window can shift based on planned duration. Updates normalize status from progress: 0 is `Open`, 1-99 is `In progress`, 100 is `Done`. Backward progress is rejected. Create/update/delete recalculate parent stage progress from active subtask average; no active subtasks resets stage progress to 0.

### 11.11 Reminders and Reminder Rules

Manual reminders:

- Must reference an existing RFQ.
- Optional stage link must belong to same RFQ.
- Due date cannot be in past.
- RFQ-level due date must be between today and RFQ deadline.
- Stage-linked due date must fit the stage window.
- Missing assignee defaults to stage assigned team or RFQ owner.
- Created reminders have `status=open`, `source=manual`, `send_count=0`.

Automatic reminders:

- `NotificationService.process_due_reminders()` first reconciles active rules.
- Supported scopes: `all_rfqs`, `critical_only`, `stage_overdue`.
- Active rules generate/deduplicate automatic reminders.
- Inactive rules resolve active automatic reminders.
- Unsupported rule scopes are counted as skipped.
- Due reminders are normalized to open/overdue, rate-limited by same-day `last_sent_at`, and capped by `max_sends` default 3.
- Delivery is log-only; no outbound provider exists.
- Automatic reminders cannot be manually resolved; manual reminders can.

### 11.12 Stats and Analytics

RFQ stats:

- `total_rfqs_12m`: RFQs created in last 365 days.
- `open_rfqs`: active status `In preparation`.
- `critical_rfqs`: critical and active.
- `avg_cycle_days`: decided RFQs only, based on max stage `actual_end` minus RFQ `created_at`.

Analytics:

- `win_rate`: Awarded / (Awarded + Lost).
- `by_client`: top 20 clients by RFQ count.
- Margin and estimation accuracy fields intentionally return `None` until reliable source data exists.

Reminder stats:

- Open tasks, overdue tasks, due this week, and RFQs with active reminders.

### 11.13 Export

`GET /rfqs/export` uses the same RFQ filters/sort as list, fetches all matching rows, and emits CSV with columns: RFQ Code, Name, Client, Priority, Status, Progress (%), Deadline, Owner, Created At.

### 11.14 Health, Metrics, Observability

- `GET /health`: liveness, public, not in schema.
- `GET /metrics`: Prometheus text, public, not in schema.
- Request IDs: incoming `X-Request-ID` accepted if 8-128 chars and safe pattern; `X-Correlation-ID` accepted as alias; otherwise UUID generated.
- Response includes `X-Request-ID`, including error responses.
- Logs include request id via logging record factory.
- Metrics count requests by method, route template, status class and record duration by method/route.

## 12. Lifecycle Rules and Invariants

Future agents must preserve these supported invariants:

- RFQ creation must create at least one valid stage instance.
- New stages should persist `stage_template_id`.
- First created stage must be `In Progress` and become `rfq.current_stage_id`.
- Stage orders are sequential after customizable workflow skip filtering.
- `rfq_code` allocation must remain atomic and monotonic per prefix.
- Deadlines must not be in the past and must fit selected workflow durations.
- Standard RFQ PATCH must not accept status transitions.
- Terminal RFQs must reject standard metadata lifecycle updates.
- Only current active stage can advance.
- Blocked stages cannot advance.
- Mandatory stage fields must be satisfied before advance.
- Incomplete active subtasks must block advance.
- Manual stage progress updates are rejected.
- Stage advance must not mutate state on validation failure.
- Go/No-Go No-Go cancellation must require explicit confirmation and reason.
- Last-stage completion must require explicit Awarded/Lost outcome.
- Lost terminal outcome must require a reason; `other` must include detail.
- `current_stage_id` must clear for terminal RFQs.
- RFQ lifecycle progress is based on completed non-skipped stages, not partial active stage workload.
- Reminder processing must remain bounded by max sends and daily rate limit.
- Manual reminders and automatic reminders must keep distinct resolution rules.
- File paths must remain contained under `FILE_STORAGE_PATH`.
- File delete is soft delete and must not physically remove files unless implementation intentionally changes with tests.
- Migrations must stay reproducible and account for branch/merge history.

Risks where an invariant should exist or remain stronger:

- No durable outbox; event publication can be lost after DB commit.
- No DB-level invariant enforces one current stage per RFQ or stage order uniqueness per RFQ.
- `rfq_history` is dormant, so persisted audit history is not available.
- Concurrent stage advance is not explicitly locked in controller code.

## 13. Integration Seams

- `rfq_ui_ms`: consumes the manager API for RFQ lists/details, workflow catalog, stage workspace, files, reminders, stats, and analytics. UI behavior must not be moved into this service.
- `rfq_intelligence_ms`: should consume operational truth through APIs/events and should not write directly to manager DB. Manager only exposes file-derived milestone flags and lifecycle events.
- IAM/auth: manager resolves bearer tokens through the IAM connector unless explicit bypass is enabled. Permissions are enforced per route and team checks are enforced in stage/file controllers.
- Event bus: manager publishes `rfq.created`, `rfq.status_changed`, `rfq.deadline_changed`, and `stage.advanced` envelopes to `EVENT_BUS_URL`, best-effort and post-commit.
- Metrics/monitoring: manager exposes `/metrics` and request-correlated logs. No external metrics exporter is configured.
- File storage: manager currently stores local filesystem files under `FILE_STORAGE_PATH`. Other services should access files through manager endpoints or documented contracts, not by writing manager storage directly.

`rfq_manager_ms` provides operational truth. Other services must not write directly to its database.

## 14. Configuration and Environment Variables

| Name | Purpose | Required/optional | Local example if safe | Security notes |
|---|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy/Alembic DB URL | Required | `postgresql+psycopg2://rfq_user:changeme@localhost:5432/rfq_manager_db` | Treat credentials as secret; app fails fast if missing/invalid |
| `APP_ENV` | Environment label | Optional, default `development` | `development` | Informational in current code |
| `APP_PORT` | Intended port | Optional, default `8000` | `8000` | Docker command passes port explicitly |
| `APP_DEBUG` | SQLAlchemy SQL echo | Optional, default `false` | `true` | Avoid in production logs |
| `IAM_SERVICE_URL` | IAM auth resolution base URL | Optional, required when bypass false in practice | `http://localhost:8001/iam/v1` | Do not bypass auth in production |
| `EVENT_BUS_URL` | HTTP event bus endpoint | Optional | `http://localhost:8002/events/v1` | Publish is best-effort |
| `FILE_STORAGE_PATH` | Local upload storage root | Optional, default `./uploads` | `./uploads` | Must be writable; path containment enforced |
| `CORS_ORIGINS` | Comma-separated CORS origins | Optional, default `*` | `http://localhost:3000` | Use explicit origins outside dev |
| `JWT_SECRET` | Reserved future seam | Optional, default dev secret | `change-me-in-production` | Do not rely on it for current auth; never commit real secrets |
| `MAX_FILE_SIZE_MB` | Upload size limit | Optional, default `50` | `50` | Enforced before writing upload |
| `AUTH_BYPASS_ENABLED` | Enables local/dev auth bypass | Optional, default `false` | `true` in scenario compose | Must be false in production |
| `AUTH_BYPASS_USER_ID` | Bypass actor id | Optional | `v1-demo-user` | Local/dev only |
| `AUTH_BYPASS_USER_NAME` | Bypass actor display name | Optional | `System` | Local/dev only |
| `AUTH_BYPASS_TEAM` | Bypass actor team | Optional | `workspace` or `Estimation` | Affects stage advance/file delete team checks |
| `AUTH_BYPASS_PERMISSIONS` | Bypass permissions CSV | Optional | `rfq:*,workflow:*,rfq_stage:*,subtask:*,reminder:*,file:*` | Powerful; local/dev only |
| `AUTH_BYPASS_DEBUG_HEADERS_ENABLED` | Allows `X-Debug-*` actor overrides in bypass mode | Optional, default `false` | `false` | Dangerous outside local debugging |
| `IAM_REQUEST_TIMEOUT_SECONDS` | IAM connector timeout | Optional, default `3.0` | `3.0` | Keep bounded |
| `EVENT_BUS_REQUEST_TIMEOUT_SECONDS` | Event publish timeout | Optional, default `3.0` | `3.0` | Keep bounded to avoid request stalls |
| `AZURE_BLOB_CONNECTION_STRING` | Mentioned only in `.env.example` comment | Not implemented | none | Do not document as supported until code exists |

## 15. Seeding and Scenario Data

`scripts/bootstrap_base_data.py`:

- Runs Alembic migrations when called through helper.
- Seeds base workflows:
  - `GHI-LONG`: fixed long workflow, 11 stages.
  - `GHI-SHORT`: fixed short workflow, 6 stages.
  - `GHI-CUSTOM`: customizable workflow using `GHI-LONG` as base catalog.
- Seeds reminder rules:
  - `Internal due soon` scope `all_rfqs`, active.
  - `Internal overdue alert` scope `stage_overdue`, active.
  - `Critical RFQ follow-up` scope `critical_only`, active.
  - `External client follow-up` scope `external_followup`, inactive and unsupported by current batch logic.

`scripts/seed_rfqmgmt_scenarios.py`:

- Seeds deterministic RFQ scenario portfolio.
- Uses `RfqController.create`, so runtime stage creation/code rules are exercised.
- Applies curated stage states, notes, subtasks, reminders, files, captured data, and terminal statuses.
- Emits manifest `seed_outputs/rfqmgmt_manager_manifest.json` by default.
- Preserves manual-only golden scenario `RFQ-06`.
- Supports batches `must-have`, `later`, `optional`, `all`.
- Is designed to be idempotent for existing scenario keys.

Safe reset/reseed:

```powershell
python ..\scripts\rfqmgmt_scenario_stack.py down --remove-volumes
python ..\scripts\rfqmgmt_scenario_stack.py all --seed-set full
```

For direct script usage, set `DATABASE_URL`, then:

```powershell
python scripts\seed_rfqmgmt_scenarios.py --batch all --reset
```

Do not run scenario RFQ seeds in production-like environments.

## 16. Tests and Validation

Test organization:

- `tests/unit/test_rfq_controller.py`: RFQ create/update/cancel, workflow customization, code allocation events, deadlines, terminal protections.
- `tests/unit/test_rfq_stage_controller.py`: stage update/advance, blockers, mandatory fields, terminal outcome, no-go cancellation, team checks, events.
- `tests/unit/test_subtask_controller.py`: due-date windows, progress/status normalization, soft delete rollup.
- `tests/unit/test_reminder_controller_actor_attribution.py`: reminder validation, assignee defaults, resolve behavior.
- `tests/unit/test_notification_service.py`: automatic reminders, due processing, rate limits, max sends.
- `tests/unit/test_auth_enforcement.py` and auth bypass/actor propagation tests: permissions and IAM/bypass behavior.
- `tests/unit/test_event_bus_connector.py`, `test_iam_service_connector.py`: connector error mapping.
- `tests/unit/test_observability_baseline.py`: request IDs and metrics.
- `tests/unit/test_h5_dormant_model_decisions.py`: dormant table decisions.
- `tests/unit/test_rfqmgmt_scenario_seed.py` and `test_seed_runtime_sync.py`: scenario seed behavior.
- `tests/integration/test_api_layer.py`: route/request validation and controller wiring.
- `tests/integration/test_fs01_file_roundtrip.py`: upload/list/download/delete and legacy path support.

Commands:

```powershell
pip install -r requirements-dev.txt
$env:PYTHONIOENCODING = "utf-8"
python scripts\verify.py
```

Direct tests:

```powershell
$env:DATABASE_URL = "sqlite:///./.quality_gate.db"
$env:PYTHONPATH = "."
python -m pytest -q
```

Observed validation result on this inspection:

- `PYTHONIOENCODING=utf-8 python scripts\verify.py`: passed.
- 240 tests passed.
- 107 warnings, mainly Pydantic class `Config` deprecation, FastAPI `on_event` deprecation, and `python_multipart` import warning.
- Without UTF-8 output encoding on Windows, `scripts/verify.py` can fail after successful checks because its final success checkmark cannot be encoded by `cp1252`.

## 17. Known Gaps, Risks, and Backlog

| Gap / Risk | Severity | Evidence | Suggested Fix |
|---|---|---|---|
| Current OpenAPI YAML is stale | Important but non-blocking | Code has `/rfqs/{id}/cancel`, `/reminders/{id}/resolve`, `/metrics`; YAML search did not show them | Regenerate/update OpenAPI and derived HTML/Postman docs |
| README endpoint counts are stale | Important but non-blocking | README says 31 business endpoints plus operational; code has 32 business route handlers plus health/metrics | Update README after this source-of-truth |
| `migrations/env.py` omits `rfq_code_counter` import | Important but non-blocking | `tests/conftest.py` imports it; Alembic env does not | Add import before future autogenerate work |
| Event publishing is not durable | Important but non-blocking | Connector is best-effort post-commit; failures logged only | Add outbox/retry if delivery becomes guaranteed requirement |
| `rfq_history` dormant | Important but non-blocking | ADR and tests confirm no active writes | Activate only with explicit audit requirements and tests |
| `rfq_stage_field_value` dormant | Important but non-blocking | ADR and tests confirm captured_data is source of truth | Keep dormant or migrate with clear ownership plan |
| No real reminder delivery provider | Important but non-blocking | `NotificationService` logs sends; test endpoint says log-only | Add connector/provider abstraction if outbound delivery needed |
| Minimal observability | Nice-to-have | Only request IDs and Prometheus HTTP metrics | Add tracing/log export when platform requires it |
| Windows verifier encoding issue | Nice-to-have | First verifier run failed only on final success checkmark under cp1252 | Replace checkmark with ASCII or force UTF-8 |
| FastAPI `on_event` deprecation | Nice-to-have | Test warnings | Move startup logging to lifespan |
| Pydantic class `Config` deprecations | Nice-to-have | Test warnings | Use `ConfigDict(from_attributes=True)` |
| Concurrent stage advance not explicitly locked | Important but non-blocking | Controller checks current stage but no row lock/version field found | Add DB locking/idempotency tests if concurrent users become likely |
| File storage is local-only | Important but non-blocking | Code uses filesystem path helpers; Azure only appears as env comment | Add storage connector if blob storage is required |
| Physical file remains after soft delete | Nice-to-have | `FileDatasource.soft_delete` only sets `deleted_at` | Keep as-is unless product/security wants physical purge semantics |
| Unsupported reminder rule scopes can exist | Nice-to-have | `external_followup` seeded inactive; service counts unsupported active scopes as skipped | Add explicit validation or implementation for new scopes |

## 18. Documentation vs Implementation Drift

| Documented Claim | Actual Implementation | Risk | Suggested Fix |
|---|---|---|---|
| README and architecture docs say 31 endpoints | Code has 32 business endpoints plus `/health` and `/metrics` | Agents may miss cancel/resolve/metrics behavior | Update README/docs and OpenAPI |
| OpenAPI YAML does not list `/rfqs/{rfq_id}/cancel` | Route and tests exist | Clients generated from YAML cannot cancel RFQs | Add endpoint to YAML |
| OpenAPI YAML does not list `/reminders/{reminder_id}/resolve` | Route and tests exist | Clients generated from YAML cannot resolve reminders | Add endpoint to YAML |
| OpenAPI YAML excludes `/metrics` | Code exposes `/metrics`, intentionally `include_in_schema=False` | Low, if intentional | Document as operational endpoint outside schema |
| README database table count says 11 tables total | Models package and DB include 12 tables including `rfq_code_counter` | Schema misunderstanding | Update README table/count |
| `.env.example` comments mention Azure Blob | No Azure storage connector exists | False expectation of supported storage backend | Remove or label as future placeholder |
| README says `.github/workflows/ci.yml`; file exists under service | Confirmed present | No risk | Keep |
| Historical archive docs/Postman mention old stage counts/status strings | Current code and seed workflows differ | Agents may follow archive by mistake | Treat `docs/archive/` as historical only |

## 19. Rules for Future AI Coding Agents

- Read this file first.
- Inspect the matching route, controller, datasource, model, translator, and tests before editing.
- Preserve BACAB layering.
- Never put business logic in routes.
- Never query the DB from routes.
- Never move chatbot, LLM, workbook parsing, MR/package parsing, or intelligence behavior into manager.
- Never change lifecycle rules without focused tests.
- Never change API contracts without updating OpenAPI/docs/tests.
- Never create migrations without checking the full migration history and current heads.
- Never bypass `RfqController.create` for scenario seed RFQ creation unless deliberately testing lower layers.
- Never make RFQ PATCH a lifecycle status backdoor.
- Never write to dormant tables unless the ADR is superseded and tests are added.
- Never expose raw stored file paths as the primary API contract.
- Never make event publication failure roll back already committed business writes unless architecture changes to a durable outbox.
- Always run tests before claiming success.
- Update this source-of-truth file when behavior changes.

## 20. Quick Start

Create virtual environment and install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Configure env:

```powershell
Copy-Item .env.example .env
# Edit DATABASE_URL and any local settings.
```

Run migrations:

```powershell
alembic upgrade head
```

Seed base/scenario data:

```powershell
python scripts\seed_rfqmgmt_scenarios.py --batch all
```

Start app:

```powershell
uvicorn src.app:app --reload --port 8000
```

Run tests:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts\verify.py
```

Open Swagger/docs:

```text
http://localhost:8000/docs
```

Run Docker scenario stack:

```powershell
python ..\scripts\rfqmgmt_scenario_stack.py all --seed-set full
```

Manager scenario API:

```text
http://localhost:18000
```

Stop/reset scenario stack:

```powershell
python ..\scripts\rfqmgmt_scenario_stack.py down --remove-volumes
```

## 21. Safe Change Playbooks

### 21.1 Add a New RFQ Field

Update ORM model, migration, Pydantic request/response schemas, translator mappings, datasource filters/sorts if applicable, controller validation, seed data if needed, tests, OpenAPI, and this document. Preserve PATCH lifecycle protections.

### 21.2 Add a New Endpoint

Add route for HTTP parsing/auth only, controller method for behavior, datasource method for DB access, schemas/translators for request/response, tests at route and business layer, OpenAPI/docs, and app router inclusion if it is a new router.

### 21.3 Change Stage Transition Logic

Start in `RfqStageController.advance` and `src/utils/rfq_lifecycle.py`. Update tests for blockers, current-stage checks, mandatory fields, subtasks, team access, no-go, terminal outcomes, progress, current_stage_id, events, and rollback/no-mutation failures.

### 21.4 Change Reminder Behavior

Inspect `ReminderController`, `ReminderDatasource`, `NotificationService`, `Reminder`/`ReminderRule`, and reminder translator. Cover due-date windows, automatic/manual distinction, rule reconciliation, status normalization, rate limiting, max sends, and resolve semantics.

### 21.5 Change File Upload Behavior

Inspect `rfq_stage_route.upload_file`, `RfqStageController.upload_file`, `FileController`, `FileDatasource`, `file_storage` helpers, and file translators. Preserve path containment, filename sanitization, size checks, soft delete semantics, auth/team checks, and file roundtrip tests.

### 21.6 Add a New Analytics Metric

Put DB aggregation in `RfqDatasource` or a clearly justified service, expose through controller/translator schema, add tests for query behavior and null/empty cases, update OpenAPI/docs, and coordinate UI contract expectations.

## 22. Final Architectural Verdict

Strong:

- Clear BACAB layering is mostly respected.
- RFQ creation and stage advancement are well covered by tests.
- Lifecycle backdoors are actively blocked.
- Scenario seeds use runtime controllers, which keeps demo data aligned with real behavior.
- Auth, request IDs, and metrics have concrete implementation and tests.

Fragile:

- OpenAPI/docs are behind code.
- Event publication is non-durable.
- Alembic model import coverage has a gap for `rfq_code_counter`.
- Audit and normalized stage field tables are schema-present but intentionally dormant.
- Local file storage and concurrent advancement need stronger production hardening if usage grows.

Must be protected:

- `current_stage_id` consistency.
- Workflow-driven stage instantiation.
- Atomic RFQ code generation.
- Stage advancement guards.
- Explicit terminal outcome and cancellation paths.
- BACAB layering.
- Boundary between manager and intelligence/chatbot responsibilities.

Best next improvement:

Update OpenAPI/README to match code, then fix the Alembic `rfq_code_counter` import and the Windows verifier encoding issue. These are low-risk, high-signal cleanup items that will prevent future agents and generated clients from working against stale truth.
