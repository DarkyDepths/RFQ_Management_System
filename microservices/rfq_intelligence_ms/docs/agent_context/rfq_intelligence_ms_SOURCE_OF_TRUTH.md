# rfq_intelligence_ms — Source of Truth for AI Agents

## 1. Purpose of This Document

This document is the canonical technical context for future AI coding agents working on `rfq_intelligence_ms`. It is based on the repository implementation first, then migrations, tests, scripts, OpenAPI/docs, and finally careful architectural interpretation where the code leaves a seam. If another document disagrees with observed code, this document records the mismatch in section 20.

## 2. Service Summary

`rfq_intelligence_ms` is a FastAPI analytical microservice that derives deterministic intelligence artifacts around RFQs owned by `rfq_manager_ms`. It consumes manager context and manual/event-shaped lifecycle triggers, parses MR source packages and GHI estimation workbooks where local inputs are resolvable, persists versioned JSON artifacts in its own database, and exposes read surfaces for snapshots, briefings, workbook profiles, parser reports, review reports, and batch seed run summaries.

## 3. Business Role

This service exists to turn RFQ operational facts and uploaded estimating material into structured evidence for UI, review, and future analytical use. It does not decide lifecycle state. Its job is to extract, compare, flag, and assemble derived artifacts such as an intake profile, intelligence briefing, workbook profile, cost breakdown, workbook review report, analytical record, parser report, and consumer-facing snapshot. The implementation follows a "deterministic before probabilistic" posture: file inventory, folder naming, sheet anchors, fixed cell ranges, parser contracts, and cross-checks come before any future LLM layer. No LLM provider integration is implemented in code.

## 4. Ownership Boundary

### 4.1 What rfq_intelligence_ms Owns

- Versioned intelligence artifact persistence in the `artifacts` table.
- Artifact types listed in `src/utils/constants.py`: `rfq_intake_profile`, `intelligence_briefing`, `workbook_profile`, `cost_breakdown_profile`, `parser_report`, `workbook_review_report`, `rfq_intelligence_snapshot`, and `rfq_analytical_record`.
- Deterministic MR package parsing under `src/services/package_parser/`.
- Deterministic GHI `.xls` workbook parsing under `src/services/workbook_parser/`.
- Manual lifecycle trigger bridge endpoints under `/intelligence/v1/rfqs/{rfq_id}/trigger/*`.
- Event-shaped processing for `rfq.created`, `workbook.uploaded`, and `outcome.recorded`.
- Idempotency tracking for inbound event envelopes in `processed_events`.
- Snapshot/read-model assembly from current artifacts.
- Batch workbook seed run summaries in `batch_seed_runs`.
- Scenario seeding of direct intelligence artifacts from a manager scenario manifest.
- Manager read connector behavior used to fetch RFQ metadata and file references.

### 4.2 What rfq_intelligence_ms Does Not Own

- RFQ lifecycle truth: status, workflow, stages, current stage, deadlines, blockers, owner, and reminders belong to `rfq_manager_ms`.
- Manager file upload ownership and canonical storage.
- Frontend UI behavior and navigation.
- Chatbot reasoning or conversational policy.
- Estimator judgment or bid approval decisions.
- IAM/authentication policy.
- Event bus infrastructure.
- Semantic PDF understanding, document intelligence, predictive learning, benchmarking, and similarity search. These are represented as deferred or unavailable where mentioned.

### 4.3 Partial Seams / Stubs

| Seam / Stub | Current implementation |
| --- | --- |
| Event bus | `src/event_handlers/lifecycle_handlers.py` processes event-shaped dicts, but no autonomous consumer/poller/webhook is wired. Manual HTTP triggers call these handlers. |
| Manager integration | `ManagerConnector` is implemented as a read-only HTTP/local-fixture seam. It calls manager APIs and can resolve mounted upload paths or local fixture aliases. No auth headers are present. |
| Manual reprocess | `/reprocess/intake` and `/reprocess/workbook` return accepted stub messages; they do not run the full chain. |
| IAM/auth | No auth dependencies, IAM client, permissions, or token checks were found. |
| Metrics | No Prometheus/OpenTelemetry metrics endpoint was found. |
| LLM | Only TODO/doc text mentions LLM as future. No provider, prompt, or LLM call exists. |
| EnrichmentService | `src/services/enrichment_service.py` is a NotImplemented stub and is not wired in `app_context.py`; implemented analytical record enrichment lives in `AnalyticalRecordService`. |
| File storage | Intelligence reads manager references and mounted paths; it does not own upload storage. |

## 5. Current Implementation Snapshot

| Item | Observed value |
| --- | --- |
| Framework | FastAPI 0.115.0 |
| Runtime/language | Python 3.11 via Dockerfile `python:3.11-slim` |
| Database | PostgreSQL in Docker; SQLAlchemy sync ORM; SQLite fallback used by tests |
| API prefix | `/intelligence/v1` for main routers; `/health` at root |
| Resource families | Health, artifact reads, manual reprocess, manual lifecycle triggers, workbook parser dev endpoint, batch seed run reads |
| Number of endpoints | 14 confirmed route handlers: 1 health, 7 intelligence reads/reprocess, 3 lifecycle triggers, 1 workbook parser, 2 batch seed run reads |
| Main tables | `artifacts`, `processed_events`, `batch_seed_runs` |
| Parser modules | `workbook_parser` and `package_parser` under `src/services/` |
| Artifact types | 8 in constants/code |
| Migrations status | Linear Alembic chain `001 -> 002 -> 003 -> 004`; note migration env imports only `Artifact` model |
| Test status | `python -m pytest -q` collected 118 tests: 64 passed, 48 failed, 6 skipped on this workstation. Failures were dominated by missing `local_fixtures` package/workbook files. |
| Docker status | `Dockerfile`, `docker-compose.yml`, and `docker-compose.scenario.yml` present; compose applies Alembic then starts uvicorn |
| CI status | Could not confirm from repository. |
| Implementation maturity | Operational deterministic vertical slices with real parsers and artifact persistence, plus documented stubs/seams for event bus, auth, LLM, and full reprocess. |

## 6. Repository Structure

Actual important structure:

```text
rfq_intelligence_ms/
  README.md
  Dockerfile
  docker-compose.yml
  docker-compose.scenario.yml
  alembic.ini
  pytest.ini
  requirements.txt
  requirements-dev.txt
  .env.example
  docs/
    rfq_intelligence_ms_openapi.yaml
    rfq_intelligence_ms_event_contracts_v1.html
    workbook_parser_*.html
    mr_package_intelligence_*.html
    agent_context/
  migrations/
    env.py
    versions/001_create_artifacts_table.py
    versions/002_add_unique_current_artifact_index.py
    versions/003_create_processed_events_table.py
    versions/004_create_batch_seed_runs_table.py
  scripts/
    seed_rfqmgmt_intelligence.py
    run_historical_workbook_batch_seed.py
    export_workbook_visualization.py
  src/
    app.py
    app_context.py
    database.py
    config/settings.py
    routes/
    controllers/
    datasources/
    models/
    translators/
    connectors/
    event_handlers/
    services/
    utils/
  tests/
    package_parser/
    workbook_parser/
    test_*_flow.py
    test_*_service.py
    test_*_routes.py
```

Roles:

- `src/app.py`: FastAPI entry point, middleware, exception handlers, and router registration.
- `src/app_context.py`: dependency composition root for datasources, connector, services, handlers, controllers, and parser orchestrator.
- `src/database.py`: sync SQLAlchemy engine/session/Base setup and `get_db`.
- `src/routes/`: thin HTTP handlers.
- `src/controllers/`: HTTP-facing orchestration controllers.
- `src/event_handlers/`: event-shaped inbound adapter for lifecycle event dicts.
- `src/datasources/`: database access only.
- `src/models/`: ORM models and minimal Pydantic transport schemas.
- `src/translators/`: artifact ORM to API dict mapping.
- `src/connectors/`: external system seams; currently manager read connector.
- `src/services/`: artifact orchestration, parser modules, lifecycle-domain operations, and batch seed logic.
- `src/utils/`: constants and exception helpers.
- `migrations/`: Alembic revision chain.
- `scripts/`: scenario seeding, historical workbook batch parsing, visualization export.
- `tests/`: API/service/event/parser/database invariant coverage.

## 7. BACAB Architecture Mapping

| Layer | Responsibility in this repo | Actual examples | Future agents must not do |
| --- | --- | --- | --- |
| `routes/` | Expose HTTP endpoints, parse request/path/body, call controllers. | `intelligence_routes.py`, `manual_lifecycle_routes.py`, `workbook_parser_routes.py`, `batch_seed_run_routes.py`, `health_routes.py`. | Do not parse Excel/ZIP, query DB, create artifacts, or decide lifecycle flow in routes. |
| `controllers/` | Application-level orchestration for HTTP requests. | `ManualLifecycleController` builds event envelopes; `WorkbookParseController` calls orchestrator; `ReprocessController` calls stub services. | Do not put low-level parser logic, raw SQL, or HTTP response formatting here. |
| `event_handlers/` | Inbound non-HTTP adapter for event-shaped lifecycle dicts. | `LifecycleHandlers.handle_rfq_created`, `handle_workbook_uploaded`, `handle_outcome_recorded`. | Do not duplicate manager lifecycle state; do not bypass idempotency. |
| `datasources/` | Database queries and persistence. | `ArtifactDatasource`, `ProcessedEventDatasource`, `BatchSeedRunDatasource`. | Do not embed parser rules, business orchestration, or manager HTTP calls. |
| `models/` | ORM entities, Pydantic route schemas, parser contract dataclasses. | `Artifact`, `ProcessedEvent`, `BatchSeedRun`, `WorkbookParseEnvelope`, `PackageParseEnvelope`. | Do not orchestrate workflows from models. |
| `translators/` | Map ORM/internal data to API/domain response shapes. | `ArtifactTranslator.to_response`, `to_summary`. | Do not run queries or parsing in translators. |
| `connectors/` | External seams. | `ManagerConnector` reads manager APIs, resolves manager uploads and local fixtures. | Do not place extraction rules or lifecycle ownership here. |
| `services/` | Intelligence-domain orchestration and specialized deterministic parsing. | `IntakeService`, `WorkbookService`, `BriefingService`, `ReviewService`, `SnapshotService`, parser modules. | Do not make services mutate manager lifecycle state or hide DB access outside datasources. |
| `utils/` | Shared constants/exceptions. | `constants.py`, `exceptions.py`. | Do not turn utils into a business logic layer. |
| `config/` | Settings loading and validation. | `Settings`, `build_settings`. | Do not read secrets outside typed config unless a narrow seam requires it. |
| `app_context.py` | Dependency wiring/composition root. | `get_artifact_datasource`, `get_lifecycle_handlers`, `get_workbook_parse_controller`. | Do not instantiate dependencies ad hoc in routes. |
| `app.py` | FastAPI factory and startup surface. | CORS, exception handlers, router inclusion. | Do not place domain logic in app creation. |

Golden flow:

```text
HTTP request / event
-> route or event entrypoint
-> controller
-> service orchestration
-> parser/extractor/scanner/checker when needed
-> datasource/connector
-> model/artifact
-> translator/response
```

## 8. Dependency Wiring and App Startup

- `src/app.py` defines `create_app()` and a module-level `app = create_app()`.
- App metadata: title `rfq_intelligence_ms`, version `0.1.0`.
- CORS origins come from comma-separated `settings.CORS_ORIGINS`.
- Exception handlers convert `AppError` to `{"detail": message}`, validation errors to 422, and unhandled exceptions to 500.
- `/health` is included at root.
- An APIRouter with prefix `/intelligence/v1` includes `intelligence_router`, `batch_seed_run_router`, `manual_lifecycle_router`, and `workbook_parser_router`.
- `src/database.py` creates one sync SQLAlchemy engine using `settings.DATABASE_URL`, `SessionLocal`, `Base`, and a generator `get_db()` that closes sessions but does not auto-commit.
- `app_context.py` wires dependencies with FastAPI `Depends`. Datasources receive `Session`; services receive datasources/connectors; controllers receive services. `LifecycleHandlers` is composed from services and event processing.
- Health is exposed; metrics are not exposed.
- No request ID or correlation ID middleware was found.

## 9. Domain Model and Database

ORM models:

| Model | Table | Key fields and constraints |
| --- | --- | --- |
| `Artifact` | `artifacts` | UUID `id`; UUID `rfq_id`; `artifact_type`; integer `version`; `status`; `is_current`; JSON/JSONB `content`; source event fields; `schema_version`; timestamps. Unique `(rfq_id, artifact_type, version)`. Partial unique current index on `(rfq_id, artifact_type)` where `is_current = true`. |
| `ProcessedEvent` | `processed_events` | Integer `id`; unique `event_id`; `event_type`; string `rfq_id`; `status`; started/completed/failed timestamps; `error_message`; timestamps. |
| `BatchSeedRun` | `batch_seed_runs` | String UUID-like `id`; unique `run_id`; parser/freeze versions; timing; input scope; counts; `overall_status`; JSON failure/warning samples. |

Important Pydantic schemas:

- `HealthResponse`, `ArtifactSummary`, `ArtifactResponse`, `ArtifactListResponse`, `ReprocessResponse` in `src/models/schemas.py`.
- Route-local request models: `TriggerWorkbookRequest`, `TriggerOutcomeRequest`, `WorkbookParseRequest`.

Important parser contract dataclasses:

- Workbook: `WorkbookParseEnvelope`, `WorkbookProfile`, `CostBreakdownProfile`, `ParserReport`, `ParserIssue`, `AnchorCheck`, `CrossCheck`, sheet report models, and per-sheet row/summary models.
- Package: `PackageParseEnvelope`, `PackageInventory`, `SectionRegistry`, `PackageIdentity`, `StandardsProfile`, `BomProfile`, `RvlProfile`, `Sa175Profile`, `ComplianceProfile`, `DeviationProfile`, `PackageParserReport`.

Enums/statuses are type literals/constants rather than database enums:

- Artifact statuses: `pending`, `partial`, `complete`, `failed`.
- Event types: `rfq.created`, `workbook.uploaded`, `outcome.recorded`.
- Parser statuses: `parsed_ok`, `parsed_with_warnings`, `failed`.
- Sheet parse statuses: `parsed_ok`, `parsed_with_warnings`, `failed`, `skipped`.
- Issue severities: `info`, `warning`, `error`.
- Check statuses: `pass`, `warn`, `fail`, `skipped`.

ERD-style summary:

```text
rfq_manager_ms.rfq (external operational truth)
  <- referenced by UUID string/UUID only, no foreign key
artifacts
  rfq_id + artifact_type + version history
  exactly one current artifact per rfq_id + artifact_type
processed_events
  event_id idempotency records per inbound event envelope
batch_seed_runs
  independent operational records for historical parser batch runs
```

Migration chain:

- `001`: creates `artifacts`.
- `002`: adds partial unique current artifact index.
- `003`: creates `processed_events`.
- `004`: creates `batch_seed_runs`.

Important migration note: `migrations/env.py` imports only `src.models.artifact`, so Alembic autogenerate would not see all ORM models unless imports are updated. Existing explicit revisions still create all three tables.

## 10. API Surface

No auth or permission dependency was found on any endpoint.

### Health

| Method | Path | Route file | Controller | Purpose | Request | Response | Side effects | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GET | `/health` | `health_routes.py` | None | Liveness check | None | `{status, service}` | None | `tests/test_health.py` |

### Artifact Reads and Reprocess

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GET | `/intelligence/v1/rfqs/{rfq_id}/snapshot` | `intelligence_routes.py` | `get_artifact(..., "rfq_intelligence_snapshot")` | Current consumer snapshot | `rfq_id` UUID | Artifact response with `content` | None | `test_routes_smoke.py`, `test_rfq_created_flow.py`, `test_workbook_uploaded_flow.py` |
| GET | `/intelligence/v1/rfqs/{rfq_id}/briefing` | same | `get_artifact(..., "intelligence_briefing")` | Current briefing | `rfq_id` UUID | Artifact response | None | `test_routes_smoke.py` |
| GET | `/intelligence/v1/rfqs/{rfq_id}/workbook-profile` | same | `get_artifact(..., "workbook_profile")` | Current workbook profile | `rfq_id` UUID | Artifact response | None | `test_routes_smoke.py`, `test_workbook_uploaded_flow.py` |
| GET | `/intelligence/v1/rfqs/{rfq_id}/workbook-review` | same | `get_artifact(..., "workbook_review_report")` | Current workbook review | `rfq_id` UUID | Artifact response | None | `test_routes_smoke.py`, `test_workbook_uploaded_flow.py` |
| GET | `/intelligence/v1/rfqs/{rfq_id}/artifacts` | same | `list_artifacts` | List artifact summaries for RFQ | `rfq_id` UUID | `{artifacts: [...]}` | None | `test_routes_smoke.py` |
| POST | `/intelligence/v1/rfqs/{rfq_id}/reprocess/intake` | same | `reprocess_intake` | Accepted stub for manual intake reprocess | `rfq_id` UUID | `{status: accepted, message}` | No actual reprocess | `test_routes_smoke.py` |
| POST | `/intelligence/v1/rfqs/{rfq_id}/reprocess/workbook` | same | `reprocess_workbook` | Accepted stub for manual workbook reprocess | `rfq_id` UUID | `{status: accepted, message}` | No actual reprocess | `test_routes_smoke.py` |

### Manual Lifecycle Triggers

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POST | `/intelligence/v1/rfqs/{rfq_id}/trigger/intake` | `manual_lifecycle_routes.py` | `trigger_rfq_created` | Build `rfq.created` manual envelope and process intake chain | `rfq_id` | Processed/duplicate/ignored result with artifact summaries | May create intake, briefing, analytical record, snapshot, processed event | Flow covered in handler tests; route smoke not directly found |
| POST | `/intelligence/v1/rfqs/{rfq_id}/trigger/workbook` | same | `trigger_workbook_uploaded` | Resolve workbook context and process workbook chain | Optional `workbook_ref`, `workbook_filename`, `uploaded_at` | Processed result with artifacts | May create workbook/cost/parser/review/analytical/snapshot artifacts | Handler tests in `test_workbook_uploaded_flow.py` |
| POST | `/intelligence/v1/rfqs/{rfq_id}/trigger/outcome` | same | `trigger_outcome_recorded` | Process outcome enrichment chain | `outcome`, optional `recorded_at`, `outcome_reason` | Processed result with analytical/snapshot artifacts | May create analytical record version and snapshot | `test_outcome_recorded_flow.py` |

### Workbook Parser Dev Endpoint

| Method | Path | Route file | Controller method | Purpose | Key request fields | Key response shape | Side effects | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POST | `/intelligence/v1/workbook-parser/parse` | `workbook_parser_routes.py` | `parse_workbook` | Manual/dev parse of a local workbook path | `workbook_path`, `rfq_id`, optional file/blob names | Raw `WorkbookParseEnvelope` dict | No persistence | Parser tests cover orchestrator; direct route test not found |

### Batch Seed Runs

| Method | Path | Route file | Controller method | Purpose | Request | Response | Side effects | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GET | `/intelligence/v1/batch-seed-runs/{run_id}` | `batch_seed_run_routes.py` | `get_run` | Read one batch seed run summary | `run_id` | Summary dict | None | `test_batch_seed_run_read_routes.py` |
| GET | `/intelligence/v1/batch-seed-runs` | same | `list_recent_runs` | List recent run summaries | `limit` 1..100, optional `overall_status` | `{runs: [...]}` | None | `test_batch_seed_run_read_routes.py` |

### Metrics

No metrics endpoint exists in code.

## 11. Core Workflows

### 11.1 RFQ Intake Flow

Trigger source:

- Manual HTTP trigger `/intelligence/v1/rfqs/{rfq_id}/trigger/intake`, or direct call to `LifecycleHandlers.handle_rfq_created(event)`.
- No autonomous event bus consumer is implemented.

Flow:

```text
manual_lifecycle_routes.trigger_intake
-> ManualLifecycleController.trigger_rfq_created
-> LifecycleHandlers.handle_rfq_created
-> EventProcessingService.begin_processing
-> IntakeService.get_rfq_context
-> ManagerConnector.get_rfq_context
-> IntakeService.build_intake_profile_from_rfq_created
-> BriefingService.build_briefing_from_intake
-> AnalyticalRecordService.build_initial_analytical_record
-> SnapshotService.rebuild_snapshot_for_rfq
-> EventProcessingService.mark_completed
```

Details:

- Event envelope must include `event_id`, `event_type`, `event_version`, `emitted_at`, `producer`, and `payload`.
- Payload must include `rfq_id`.
- Unsupported event types are ignored.
- Duplicate completed events return `status: duplicate` and do not create new versions.
- `ManagerConnector` reads manager RFQ detail and stage files, then filters source package refs from files with type `Client RFQ`.
- If a source package reference resolves to a local folder/ZIP, `PackageParserOrchestrator` parses it and the intake artifact becomes enriched.
- If no package path resolves, intake falls back to reference-only partial content.
- If package parsing raises, intake falls back to partial parser-failed content with explicit gaps.
- `rfq_id` is persisted as UUID; `rfq_code`, client, project title, and created time are copied as derived manager context only.
- The service does not mutate manager RFQ state.

### 11.2 MR Package / ZIP Parsing Flow

Implemented under `src/services/package_parser/`.

```text
PackageParserOrchestrator.parse(path, rfq_id)
-> ZipScanner.open_package for .zip OR TreeScanner.scan for directory
-> IdentityExtractor.extract
-> SectionClassifier.classify
-> StandardsExtractor.extract
-> BomExtractor.extract
-> RvlExtractor.extract
-> Sa175Extractor.extract
-> ComplianceExtractor.extract
-> package_parser.cross_checks.run_cross_checks
-> package_parser.assembler.build_envelope
```

Input:

- A directory package root or `.zip` file.
- ZIP scanner validates against absolute path and path traversal, extracts to a temp dir, resolves package root, then delegates to `TreeScanner`.

Scanner behavior:

- Ignores dotfiles, known system files (`.ds_store`, `thumbs.db`, `.gitkeep`, `desktop.ini`), and `__macosx`.
- Detects numbered folders matching `NN - label`.
- Detects MR index files by `MR Index...`.
- Detects MR numbers in filenames by `MR-(digits)`.
- Detects section prefixes in filenames by leading `NN_` or `NN-`.
- Classifies root files as root MR index, internal review file, or unclassified extra.

Section recognition:

- Numbered canonical map covers `0` through `15` plus heuristic alias `revision_history`.
- Canonical keys include `approval_sheet`, `mr_checklist`, `description_bom`, `rvl`, `specs_datasheets`, `project_drawings`, `applicable_standards`, `sa175_forms`, `nmr`, `spdp`, `qaqc_requirements`, `general_requirements`, `vendor_doc_requirements`, `routing_slip`, `packing_specs`, `notes_to_vendor`, and `revision_history`.
- Missing canonical sections are explicit in `section_registry.missing_canonical_sections`.

Targeted extraction:

- Identity from root name pattern `PROJECT-MR-NNN description REV-XX`.
- Standards by filename regex/folder fallback in section 06.
- BOM from `.xlsx` with `bom` in filename under section 02.
- RVL from `.docx` under section 03.
- SA-175 forms by filename under section 07.
- Compliance and deviation workbooks from `.xlsx` under section 15 / `notes_to_vendor`.

Limitations:

- Semantic PDF/content understanding is not implemented.
- Specs, QA/QC, general requirements, vendor docs, and scope meaning remain deferred.
- No LLM fallback exists.

### 11.3 Workbook Upload / Workbook Parsing Flow

Implemented for deterministic `.xls` workbook parsing.

```text
manual trigger or handler event
-> LifecycleHandlers.handle_workbook_uploaded
-> EventProcessingService.begin_processing
-> WorkbookService.get_workbook_context
-> ManagerConnector.get_workbook_context / fetch_workbook_local_path
-> WorkbookService.build_workbook_parser_artifacts_from_uploaded_event
-> parse_workbook_deterministic
-> WorkbookParserOrchestrator.parse
-> XlsWorkbookReader.open
-> TemplateMatcher.validate
-> GeneralExtractor, BidSExtractor, TopSheetExtractor
-> optional CashFlowExtractor, MatBreakupExtractor, BoqExtractor
-> workbook_parser.cross_checks.run_cross_checks
-> workbook_parser.assembler.build_envelope
-> persist workbook_profile, cost_breakdown_profile, parser_report
-> ReviewService and AnalyticalRecordService if parser did not fail
-> SnapshotService.rebuild_snapshot_for_rfq
```

Accepted file type:

- The parser reader only supports `.xls` in `XlsWorkbookReader.open`. `parse_workbook_deterministic` discovers `.xls*`, but the orchestrator reader rejects non-`.xls` suffixes.

Soft-fail behavior:

- Missing optional Pack 2 sheets (`Cash Flow`, `Mat Break-up`, `B-O-Q`) become skipped sheet reports.
- Optional extractor crashes are caught by `_try_extract` and converted to failed sheet reports/issues while core parsing continues.
- Core failure occurs if template matching fails or any of `General`, `Bid S`, or `Top Sheet` fails.
- If the event handler fails before parser artifacts are created, `WorkbookService.persist_parser_failure_artifact` persists a failed `parser_report`.

### 11.4 Workbook Sheet Extraction

#### General

- File: `src/services/workbook_parser/extractors/general_extractor.py`.
- Required sheet: `General`.
- Identity cells: inquiry no `D4`, revision `H4`, client `D5`, status `H5`, client inquiry `D6`, subject `D7`, project `D8`, inquiry date `D9`.
- Body range: rows `14:62`.
- Extracts item rows: serial, tag, revision, description, qty, dimensions, weights, material, item type, RT fields, and boolean flags such as PWHT, ASME stamp, NB registration cost, FEA, tensioner, freight, helium leak, KOM.
- Drops placeholder rows such as tag `E` and description `XXXX`.
- Emits errors for missing required identity fields and warnings for invalid yes/no flag values.

#### Bid S

- File: `bid_s_extractor.py`.
- Identity mirror cells: rows 2-6 around columns B/C.
- Bid meta: direct MH, indirect MH, exchange rate, total weight, PO date, delivery, dated/status.
- Body range: rows `14:49`.
- Extracts bid summary lines with sections `direct_cost`, `other_overheads`, and `pricing_final`.
- Maps known labels to canonical keys and promotes summary rows: total direct cost, overheads, gross cost, gross margin, gross price, escalation, negotiation, grand total.
- Unknown labels emit warnings.

#### Top Sheet

- File: `top_sheet_extractor.py`.
- Identity mirror cells: rows 2-7.
- Body range: rows `11:76`.
- Normalizes leading dash labels.
- Extracts revenue, project direct cost, project indirect cost, and profitability sections.
- Promotes summary metrics including total revenue, direct cost, contribution margin, total project cost, gross profit, BU overheads, profit before zakat/tax, zakat/tax, and PATAM.
- Unknown labels/missing promoted rows are reported as issues.

#### Cash Flow

- File: `cash_flow_extractor.py`.
- Optional sheet `Cash Flow`.
- Extracts identity mirror, cash flow lines, monthly values, total inflow/outflow percentages and SAR, net final position, months with data, negative month count, and peak negative exposure.
- Missing sheet is skipped by orchestrator; extractor tests cover missing-sheet failed result when called directly.

#### Mat Break-up

- File: `mat_breakup_extractor.py`.
- Optional sheet `Mat Break-up`.
- Extracts material decomposition by item and categories, weights, cost totals, percentages, and summary totals.
- Missing sheet is skipped by orchestrator; extractor tests cover missing-sheet failed result when called directly.

#### B-O-Q

- File: `boq_extractor.py`.
- Optional sheet `B-O-Q`.
- Extracts BOQ item blocks, component rows, grand totals, computed totals, grand-total-vs-computed match flag, and material price table.
- Missing sheet is skipped by orchestrator; crashes are converted to parser issues by orchestrator.

### 11.5 Cross-Checks

Workbook cross-checks:

| Check family | Codes / logic | Behavior |
| --- | --- | --- |
| Identity mirrors | `GENERAL_vs_BID_S_*`, `GENERAL_vs_TOP_SHEET_*` for inquiry, client, client inquiry, subject, project name | Missing side -> `skipped`; mismatch -> `warn`; exact match -> `pass`. |
| Weight/revenue/cost numeric | `GENERAL_TOTAL_WEIGHT_vs_BID_S_TOTAL_WEIGHT`, `TOP_SHEET_TOTAL_REVENUE_vs_BID_S_GRAND_TOTAL`, financial charges, escalation, negotiation, direct cost | Uses absolute or relative tolerance; missing side -> `skipped`; delta outside tolerance -> `warn`. |
| Cash flow | `CASH_FLOW_vs_GENERAL_*`, `CASH_FLOW_INFLOW_vs_BID_S_GRAND_TOTAL`, `CASH_FLOW_INFLOW_vs_TOP_SHEET_REVENUE` | Runs only when cash flow data is present. |
| Mat break-up | `MAT_BREAKUP_TOTAL_vs_BID_S_MATERIAL`, `MAT_BREAKUP_FINISH_WT_vs_BID_S_WEIGHT`, `MAT_BREAKUP_ITEM_SUM_vs_SUMMARY` | Runs only when material decomposition exists. |
| BOQ | `BOQ_ITEM_{n}_WEIGHT_vs_GENERAL` | Informational tolerance check by item when BOQ and general rows exist. |

Package cross-checks:

| Code | Inputs | Behavior |
| --- | --- | --- |
| `PACKAGE_MR_vs_RVL_MR` | package identity vs RVL MR | pass/warn/skipped exact check |
| `PACKAGE_MR_vs_BOM_MR` | package identity vs MR in BOM source filename | pass/warn/skipped |
| `PACKAGE_MR_vs_COMPLIANCE_MR` | package identity vs compliance MR | pass/warn/skipped |
| `PACKAGE_MR_vs_DEVIATION_MR` | package identity vs deviation MR | pass/warn/skipped |
| `BOM_9COM_vs_RVL_9COM` | BOM 9COM set vs RVL 9COM set | pass if overlap exists, warn if no overlap, skipped if missing |
| `BOM_9COM_vs_COMPLIANCE_9COM` | BOM 9COM set vs scalar compliance 9COM | pass if exact set equals scalar set, warn otherwise, skipped if missing |
| `SECTION_PREFIX_CONSISTENCY` | file prefixes vs section folder number | one check per prefixed file, or skipped if none |
| `MR_INDEX_COMPLETENESS` | MR index count vs numbered section count | pass if equal, warn if not, skipped if no numbered sections |

### 11.6 Artifact Assembly

- Intake profile: `IntakeService` builds either reference-only content, deterministic package enriched content, or parser-failed fallback content.
- Briefing: `BriefingService` builds either limited/stub briefing from manager context or deterministic-enriched briefing from parsed intake.
- Workbook profile: `WorkbookService` wraps parser envelope fields, workbook source, structure, template recognition, canonical estimate profile, and readiness flags.
- Cost breakdown profile: `WorkbookService` wraps `envelope.cost_breakdown_profile`.
- Parser report: `WorkbookService` wraps parser report details and workbook source.
- Workbook review report: `ReviewService` compares workbook structure and optional intake project title, while keeping benchmark analysis unavailable.
- Analytical record: `AnalyticalRecordService` creates initial, workbook-enriched, and outcome-enriched versions.
- Snapshot/read model: `SnapshotService` reads current artifacts and assembles availability matrix, panels, outcome summary, and consumer hints.
- Package parser envelope is not persisted directly as its own artifact type; it is embedded into intake-derived content.

### 11.7 Snapshot / Read Model Flow

`SnapshotService.rebuild_snapshot_for_rfq`:

- Loads current artifacts for one RFQ through `ArtifactDatasource.list_current_artifacts_for_rfq`.
- Looks for intake, briefing, workbook profile, cost breakdown, parser report, workbook review, and analytical record.
- Builds `rfq_intelligence_snapshot` with RFQ summary, availability matrix, intake/briefing/workbook/review panels, analytical status, outcome summary, consumer hints, and `overall_status: partial`.
- Snapshot is refreshed at the end of `rfq.created`, `workbook.uploaded`, and `outcome.recorded` handler flows.

### 11.8 Review Report Flow

`ReviewService.build_workbook_review_report`:

- Always creates structural completeness findings from workbook missing/extra sheets, or a low-severity "no major structural gaps" finding.
- Adds an intake-vs-workbook project title mismatch finding only when both titles are meaningful and not placeholders.
- Always includes benchmark outlier as unavailable with `insufficient_historical_base`.
- Adds a workbook internal consistency finding stating pairing is not assessed.
- Does not assert that a discrepancy is wrong; findings use review posture language.

### 11.9 Outcome / Learning Flow

`LifecycleHandlers.handle_outcome_recorded`:

- Validates envelope and payload (`rfq_id`, `outcome`, `recorded_at`).
- Allows only `awarded`, `lost`, or `cancelled`.
- Uses idempotency via `ProcessedEvent`.
- Calls `AnalyticalRecordService.enrich_analytical_record_from_outcome`.
- Rebuilds snapshot.
- Stored outcome enrichment records status, reason, recorded timestamp, source event, learning loop status, and flags benchmark/similarity/predictive as not ready.

No predictive learning or historical model update exists.

### 11.10 Health, Metrics, Observability

- `/health` returns static service health.
- Parser reports persist warnings, errors, sheet reports, anchor checks, and cross-checks.
- `processed_events` tracks event processing status and error message.
- Standard Python logging is used in parser orchestrators when optional extractions fail.
- No request ID, correlation ID middleware, metrics endpoint, structured tracing, or monitoring connector was found.

## 12. Parser Contracts and Artifact Shapes

| Contract / artifact | File path | Shape summary |
| --- | --- | --- |
| `ParserIssue` | `src/services/workbook_parser/issues.py` | `code`, `severity`, optional sheet/cell/row/field path, message, expected/actual/raw values. |
| `AnchorCheck` | same | Sheet, cell, expected normalized value, actual normalized value, pass bool. |
| `CrossCheck` | same | Code, status, left/right field paths and values, tolerances, deltas, note. |
| `SheetReport` / `SheetReports` | same | Per-sheet status, merged region count, range, scanned/kept/skipped rows, warning/error counts. |
| `WorkbookParseEnvelope` | `workbook_parser/contracts.py` | RFQ id, template name, workbook format/name/blob path, match flag, parsed_at, parser version, workbook profile, cost breakdown profile, parser report, optional BOQ profile. |
| `WorkbookProfile` | same | Primary identity, Bid S/Top Sheet mirrors, general item rows/summary, bid meta. |
| `CostBreakdownProfile` | same | Bid summary lines/summary, Top Sheet lines/summary, optional material decomposition and financial profile. |
| `PackageParseEnvelope` | `package_parser/contracts.py` | RFQ id, parser version/time/input, inventory, identity, registry, standards/BOM/RVL/SA175/compliance/deviation profiles, parser report. |
| `PackageInventory` | same | Root name, input type, file/folder counts, entries, root files, extension counts, system file count, scan time. |
| `SectionRegistry` | same | Matched sections, unmatched folders, missing canonical sections, counts, MR index count. |
| `rfq_intake_profile` | built by `IntakeService` | Artifact meta, source package, package identity/structure, document understanding, canonical project profile, evidence, quality/gaps, readiness. |
| `intelligence_briefing` | built by `BriefingService` | Artifact meta, executive summary, known/missing fields, compliance/risk placeholders or deterministic facts, section availability, next actions. |
| `workbook_profile` | built by `WorkbookService` | Artifact meta, workbook source, template info, structure, canonical estimate profile, parser profile, pairing validation, readiness. |
| `cost_breakdown_profile` | built by `WorkbookService` | Artifact meta, workbook source, template info, parser cost breakdown, parser status. |
| `parser_report` | built by `WorkbookService` | Artifact meta, workbook source, template info, parsed_at, parser report. |
| `workbook_review_report` | built by `ReviewService` | Summary, structural findings, internal consistency finding, intake-vs-workbook findings, unavailable benchmark family. |
| `rfq_intelligence_snapshot` | built by `SnapshotService` | RFQ summary, availability matrix, panels, outcome summary, consumer hints, status. |
| `rfq_analytical_record` | built by `AnalyticalRecordService` | RFQ identifiers, lineage, completeness flags, notes, workbook/outcome enrichment where present. |

## 13. Deterministic Extraction Rules

- Package root identity regex: `^([\w-]+-MR-\d+)[_\s]+(.+?)[-\s]*REV[-\s]*(\d+)\s*$`.
- Package MR short regex: `MR-\d+`.
- Numbered package folders: `NN - label`.
- Package file section prefix: leading `NN_` or `NN-`.
- ZIP extraction rejects absolute paths and path traversal.
- Package scanners ignore dotfiles and known OS/system files/folders.
- Standards filename regexes detect SAMSS, SAES, SAEP, and STD DWG references.
- BOM workbook search requires `.xlsx`, section 02, and `bom` in filename; header row is scanned in first 25 rows and must meet recognized/strong-field thresholds.
- RVL search requires `.docx` in section 03; first table with recognizable headers is parsed.
- SA-175 forms are detected by filename regex `175[-_](\d{6})`.
- Compliance/deviation extraction searches `.xlsx` files in section 15 with required filename terms.
- Workbook reader supports `.xls`; row/column coordinates are 1-based.
- Merged-cell labels return the top-left merged value.
- Date cells become `YYYY-MM-DD`; non-date cells return `None`.
- Empty/whitespace values normalize to `None`.
- Numeric normalization removes commas and returns int if integral.
- Workbook template required sheets are `General`, `Bid S`, `Top Sheet`.
- Optional workbook sheets are `Cash Flow`, `Mat Break-up`, and `B-O-Q`.
- Workbook hard anchors can fail template match; soft anchors generate warnings.
- Missing optional sheets become skipped sheet reports in assembled envelopes.
- Missing or unknown values must become `None`, skipped checks, warnings, or errors. The parser must not invent values.

## 14. Lifecycle Rules and Invariants

- Intelligence must not mutate manager lifecycle state directly.
- `rfq_manager_ms` is operational truth; intelligence stores derived artifacts only.
- Same event ID must be idempotent: completed duplicates must not create new artifact versions.
- In-progress duplicate events are ignored.
- Failed events can be retried; `EventProcessingService.begin_processing` marks previous failed records as processing.
- Artifact versioning must keep only one current artifact per RFQ/artifact type.
- Creating a new artifact version must flip the old current row to non-current before inserting the new current row.
- Parser outputs should be reproducible for the same input except generated timestamps and IDs.
- Missing/unknown parser data must be explicit as `None`, issues, gaps, skipped checks, or unavailable sections.
- Parser failures must be controlled and reported, especially in `parser_report`.
- Cross-check warnings must not silently disappear.
- Workbook parser core sheets (`General`, `Bid S`, `Top Sheet`) determine core parser failure.
- Optional workbook sheets should soft-fail without losing core artifacts.
- Snapshot must reflect unavailable sections truthfully.
- Migrations must remain linear and reproducible.

Risks where an invariant should exist but is incomplete:

- No event bus consumer enforces production delivery/idempotency outside manual/direct handler calls.
- No auth or tenant boundary prevents arbitrary trigger/read calls.
- Missing fixture files currently make many parser tests fail instead of skip.
- No explicit concurrency lock protects artifact current-version flips beyond database constraints.

## 15. Integration Seams

- `rfq_manager_ms`: read-only connector for RFQ detail, stage summaries, stage files, latest workbook file, and local upload resolution. Manager provides operational truth.
- `rfq_ui_ms`: inferred/manual trigger producer via `ManualLifecycleController`, which sets `producer: rfq_ui_ms.manual_trigger`. UI should consume HTTP contracts, not database tables.
- File upload/storage: manager owns uploads; intelligence resolves references through manager API, `MANAGER_UPLOADS_MOUNT_PATH`, direct paths, or local fixtures.
- Event bus: contract docs exist; no code-level bus consumer exists.
- IAM/auth: no implementation found.
- Metrics/monitoring: no implementation found.
- LLM provider: no implementation found.

Explicit boundary: `rfq_manager_ms` provides operational truth. `rfq_intelligence_ms` provides derived intelligence artifacts. `rfq_ui_ms` should consume intelligence through HTTP contracts, not by reading its database.

## 16. Configuration and Environment Variables

| Name | Purpose | Required/optional | Local example | Security notes |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL | Required by settings import | `postgresql+psycopg2://intelligence_user:intelligence_pass@localhost:5433/rfq_intelligence_db` | Contains credentials; do not commit real secrets. |
| `APP_NAME` | App name | Optional default `rfq_intelligence_ms` | `rfq_intelligence_ms` | Non-secret. |
| `APP_PORT` | Intended app port | Optional default `8001` | `8001` | Docker command currently hardcodes port 8001. |
| `APP_DEBUG` | SQL echo/debug flag | Optional default `false` | `false` | Avoid true in production because SQL logging may leak data. |
| `ENVIRONMENT` | Environment label | Optional default `development` | `local` | Non-secret. |
| `CORS_ORIGINS` | Comma-separated CORS origins | Optional default `*` | `*` | Restrict in production. |
| `MANAGER_MS_BASE_URL` | Base URL for manager connector | Optional default `http://localhost:18000` | `http://localhost:18000` | Non-secret; controls outbound service target. |
| `MANAGER_REQUEST_TIMEOUT_SECONDS` | HTTP timeout for manager connector | Optional default `10.0` | `10.0` | Non-secret. Not listed in `.env.example`. |
| `MANAGER_UPLOADS_MOUNT_PATH` | Mounted manager uploads root | Optional default `/app/manager_uploads` | `/app/manager_uploads` | Path only. Present in scenario compose, not `.env.example`. |
| `LOCAL_FIXTURES_DIR` | Override local fixtures root for connector | Optional | `D:\path\to\fixtures` | Path only. Used via `os.getenv`, not Pydantic settings. |

## 17. Seeding and Scenario Data

- `scripts/seed_rfqmgmt_intelligence.py` reads a manager scenario manifest and creates intelligence artifacts directly.
- Seed profiles include `early_partial`, `stale_partial`, `thin_partial_stale`, `mature_partial`, `mature_partial_stale_award`, `failed_workbook`, `failed_briefing`, and `pending_artifact`.
- The golden scenario key `RFQ-06` is reserved/manual-only.
- Seeded artifacts can include intake, briefing, workbook profile, cost breakdown, parser report, workbook review, analytical record, and snapshot depending on profile.
- `scripts/run_historical_workbook_batch_seed.py` discovers workbook files by glob, runs deterministic parser, optionally persists artifacts, and writes a `batch_seed_runs` record.
- `scripts/export_workbook_visualization.py` exports parser envelopes, event results, run summaries, and artifact JSON for a local workbook.
- Scenario compose mounts `../seed_outputs` and `../rfq_manager_ms/uploads_scenario` into the intelligence container.
- Local parser fixture paths are expected under `local_fixtures/rfq_created/...` and `local_fixtures/workbook_uploaded/...`, but those folders were not present in this checkout during test execution.

Safe reset/reseed:

```bash
docker compose down -v
docker compose up --build
alembic upgrade head
python scripts/seed_rfqmgmt_intelligence.py --manager-manifest <manifest.json>
```

Exact full platform scenario command from this workspace could not be confirmed from repository. README contains an absolute `d:\PFE\scripts\rfqmgmt_scenario_stack.py` path, which does not match this repository root.

## 18. Tests and Validation

Test organization:

- `tests/test_*_flow.py`: event/lifecycle flow coverage for RFQ created, workbook uploaded, outcome recorded.
- `tests/test_*_service.py`: intake, briefing, snapshot service coverage.
- `tests/test_*_routes.py` and `test_routes_smoke.py`: health, artifact reads, reprocess stubs, batch seed run reads.
- `tests/test_artifact_invariants.py`: current artifact uniqueness/version history.
- `tests/package_parser/`: scanner, classifier, extractors, cross-checks, ZIP, orchestrator.
- `tests/workbook_parser/`: reader, template matcher, extractors, parser orchestrator, cross-checks, batch seed runner.

Commands:

```bash
python -m pytest -q
python -m pytest tests/workbook_parser -q
python -m pytest tests/package_parser -q
```

Observed validation on April 25, 2026:

```text
python -m pytest -q
118 collected
64 passed
48 failed
6 skipped
```

Failure pattern:

- Most failures referenced missing `local_fixtures/workbook_uploaded/workbook_sample_001/ghi_workbook_32_sheets.xls`.
- Package parser failures referenced missing `local_fixtures/rfq_created/source_package_sample_001/SA-AYPP-6-MR-022_COLLECTION VESSEL - CDS-REV-00`.
- Several workbook flow tests intentionally skip when fixture is unavailable; many parser tests fail instead of skipping.

Coverage strengths:

- Artifact version/current invariants.
- Event idempotency and rollback behavior.
- Service assembly for intake/briefing/snapshot/review.
- Workbook parser contracts, sheet extractors, cross-checks, and batch seeding.
- Package parser scanner/classifier/extractors/cross-checks.

Coverage gaps:

- Route-level tests for manual trigger endpoints were not found.
- Direct route test for `/workbook-parser/parse` was not found.
- Auth/IAM and metrics cannot be covered because they are not implemented.
- Event bus consumer cannot be covered because it is not implemented.

## 19. Known Gaps, Risks, and Backlog

| Gap / Risk | Severity | Evidence | Suggested Fix |
| --- | --- | --- | --- |
| Local fixture-dependent tests fail when fixtures are absent | Important but non-blocking | `python -m pytest -q` failed 48 tests with missing `local_fixtures` paths | Commit test fixtures, generate them in test setup, or mark fixture-dependent tests with clear skip behavior. |
| No autonomous event bus consumer | Important but non-blocking | Lifecycle handlers note manual/direct only; no consumer route/process found | Add a connector/adapter with idempotency and tests. |
| No auth/IAM | Important but non-blocking | No auth dependencies in routes; README says IAM outside scope | Add auth seam before exposing write/trigger endpoints beyond trusted local use. |
| Manual reprocess endpoints are stubs | Important but non-blocking | `ReprocessController` and services return accepted stub messages | Implement explicit reprocess flow or rename/document as accepted-only. |
| OpenAPI drift: only 7 endpoint scope | Important but non-blocking | Code has 14 endpoints including triggers/parser/batch seed | Regenerate/update OpenAPI from current app. |
| OpenAPI artifact type drift | Important but non-blocking | OpenAPI omits `cost_breakdown_profile` and `parser_report` from some artifact enums | Update schemas to include all 8 current artifact types. |
| Alembic env imports only `Artifact` | Nice-to-have | `migrations/env.py` imports only `src.models.artifact` | Import all ORM models for accurate autogenerate metadata. |
| `.env.example` incomplete | Nice-to-have | Settings include timeout/upload mount; connector reads `LOCAL_FIXTURES_DIR` | Add non-secret env examples for all config knobs. |
| No metrics/request correlation | Nice-to-have | No metrics route or middleware found | Add middleware and metrics seam if operational observability is required. |
| Parser assumes `.xls` for orchestrator reader | Important but non-blocking | `XlsWorkbookReader.open` rejects non-`.xls`; scripts mention `.xls/.xlsx/.xlsm` | Either add readers for `.xlsx/.xlsm` or narrow docs/scripts. |
| Package/workbook fixture assumptions may be brittle | Important but non-blocking | Fixed sheet anchors, folder number map, sample fixture tests | Keep assumptions documented and extend with multi-sample tests. |
| No LLM hallucination risk today | Already resolved | No LLM implementation found | Preserve deterministic-first boundary if adding LLM. |
| Concurrency around artifact current flips | Important but non-blocking | DB unique index exists, but service flips old current then inserts without explicit retry | Add transaction/retry tests for concurrent artifact creation if service scales. |

## 20. Documentation vs Implementation Drift

| Documented Claim | Actual Implementation | Risk | Suggested Fix |
| --- | --- | --- | --- |
| OpenAPI says V1 cold-start scope has 7 endpoints, 6 artifact types, 1 artifact table | Code has 14 route handlers and 8 artifact types; DB also has `processed_events` and `batch_seed_runs` | Agents may miss triggers, parser endpoint, run summaries, and parser support artifacts | Regenerate OpenAPI or mark it historical. |
| OpenAPI event triggers are not modeled as REST endpoints | Code exposes manual lifecycle trigger REST endpoints under `/trigger/*` | Consumers may not discover current integration bridge | Add trigger endpoints to OpenAPI or document as internal/dev endpoints. |
| OpenAPI workbook profile mentions schedule profile | Code builds cost breakdown and financial profile from parser; no standalone schedule profile artifact/section observed | UI/agent may expect unavailable fields | Update schema to actual content or implement schedule extraction with tests. |
| README lists current endpoints but omits `/trigger/outcome`, `/workbook-parser/parse`, and batch seed routes | Code includes them | Operational/debug surfaces are underdocumented | Update README/OpenAPI endpoint list. |
| README scenario command uses `d:\PFE\scripts\...` | Current checkout is under `d:\RFQ_MANAGEMENT_SYSTEM`; no such command was confirmed here | Quick start may fail for future agents | Replace with repository-relative command if available. |
| `Artifact` model docstring says "all 6 artifact types" | Constants/code use 8 artifact types | Confusion over whether parser support artifacts are first-class | Update docstring/docs. |
| Workbook parser docs mention future/new `parsers/workbook` and translator/datasource names | Current code places parser under `src/services/workbook_parser` and the dev route returns raw envelope without translator | Agents may create duplicate parser folders/layers | Treat implementation packs as historical design docs unless code confirms. |
| Service docstrings mention LLM extraction "when needed" | No LLM calls/providers/prompts exist | Agents may assume semantic extraction exists | Keep LLM described as future seam only. |
| Some service docstrings still say TODO "wire to datasource" | Artifact persistence is implemented in current service methods | Understates maturity of vertical slices | Refresh docstrings when code changes are allowed. |

## 21. Rules for Future AI Coding Agents

- Read this file first.
- Inspect the matching route, controller, service/parser, datasource, and model before editing.
- Preserve BACAB layering.
- Never put parser logic in routes.
- Never put database logic in routes.
- Never duplicate `rfq_manager_ms` lifecycle truth in intelligence.
- Never make intelligence mutate RFQ status, workflow, stage, blocker, owner, deadline, or reminder state.
- Never invent missing intelligence values; represent missing data explicitly.
- Never hide parser issues, skipped checks, failed sheets, or unavailable analysis families.
- Never remove cross-checks without tests.
- Never change artifact schemas without migration/docs/tests/UI impact review.
- Never add LLM behavior where deterministic extraction is enough.
- Never let LLM output bypass deterministic validation if LLM is added later.
- Never create migrations without checking `migrations/versions` history.
- Always run parser tests before claiming parser success.
- Always run relevant service/API tests before claiming lifecycle success.
- Update this source-of-truth file when behavior changes.

## 22. Quick Start

Create environment and install dependencies:

```bash
cd microservices/rfq_intelligence_ms
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Configure env:

```bash
copy .env.example .env
```

Set `DATABASE_URL` in `.env`. Do not commit real credentials.

Run migrations:

```bash
alembic upgrade head
```

Start app:

```bash
uvicorn src.app:app --port 8001 --reload
```

Run tests:

```bash
python -m pytest -q
```

Run parser tests:

```bash
python -m pytest tests/workbook_parser tests/package_parser -q
```

Open Swagger:

```text
http://localhost:8001/docs
```

Run Docker:

```bash
docker compose up --build
```

Run scenario Docker:

```bash
docker compose -f docker-compose.scenario.yml up --build
```

Seed data:

```bash
python scripts/seed_rfqmgmt_intelligence.py --manager-manifest <manager_manifest.json>
```

Historical workbook batch seed:

```bash
python scripts/run_historical_workbook_batch_seed.py --input-dir <workbook_root> --output-json <result.json>
```

Could not confirm exact full-platform scenario stack command from this repository.

## 23. Safe Change Playbooks

### 23.1 Add a New Workbook Field

Inspect the relevant extractor and contract dataclass first. Add the field to `workbook_parser/contracts.py`, extract it in the sheet extractor, include it in assembler output if needed, update `WorkbookService` artifact wrapping only if the artifact surface changes, and add tests for extraction, missing value behavior, and artifact shape.

### 23.2 Add a New Sheet Extractor

Add a reader-compatible extractor under `src/services/workbook_parser/extractors/`, define result/contract fields, wire optional execution in `WorkbookParserOrchestrator`, assemble sheet report/issues in `assembler.py`, add cross-checks if the sheet provides comparable data, and test missing sheet, malformed sheet, happy path, and orchestrator soft-fail behavior.

### 23.3 Change Workbook Parser Envelope

Update `contracts.py`, `assembler.py`, any service artifact wrapping in `WorkbookService`, the dev parser route expectations, tests under `tests/workbook_parser`, OpenAPI/docs, and UI consumers. Preserve explicit parser issue and cross-check fields.

### 23.4 Add a New MR Package Section Rule

Update `SectionClassifier` maps/aliases, add or update extractor logic if the section has structured extraction, update package contracts and assembler if output changes, add synthetic tests plus fixture-based tests, and document any folder/name assumptions.

### 23.5 Add a New Cross-Check

Define inputs and status semantics first. Add the check in `workbook_parser/cross_checks.py` or `package_parser/cross_checks.py`, ensure missing data becomes `skipped`, update parser report tests, and verify warning/failure impact on parser status.

### 23.6 Add a New Intelligence Artifact

Add constant, define artifact content schema, add service builder, persist through `ArtifactDatasource`, expose via controller/route/translator if needed, include it in snapshot availability if consumer-facing, create migration only if table shape changes, and update tests/docs/OpenAPI.

### 23.7 Change Manager Integration

Edit only the connector for manager HTTP/storage behavior unless orchestration genuinely changes. Preserve read-only manager boundary, add timeout/error behavior tests, document failure fallback, and do not write to manager DB or duplicate manager lifecycle state.

### 23.8 Add LLM-Assisted Extraction

Keep deterministic extraction as primary evidence. Put prompts/provider calls behind a connector/service seam, define input/output schema, validate LLM output against deterministic anchors, store uncertainty and evidence, provide deterministic fallback, guard against hallucinated fields, and add tests for missing evidence, invalid output, and no-network/provider failure.

## 24. Final Architectural Verdict

Strong:

- The repo has clear BACAB layering for HTTP, controller, datasource, connector, service, parser, and translator responsibilities.
- Artifact versioning and current-row invariants are explicit and tested.
- Deterministic workbook and package parsing are organized into contracts, readers/scanners, extractors, assemblers, and cross-checks.
- Event-shaped flows are idempotent and transactional enough for current manual/direct-handler usage.

Fragile:

- Test reliability depends on local fixture folders not present in this checkout.
- OpenAPI and older implementation docs lag behind current code.
- Manual reprocess, event bus, IAM, metrics, semantic document understanding, and LLM are seams/stubs.
- Workbook parser reader support is narrower than some script/help text implies.

Must be protected:

- `rfq_manager_ms` remains the operational lifecycle owner.
- Missing data must stay explicit.
- Parser warnings/errors/cross-checks must remain visible.
- One current artifact per RFQ/artifact type must remain enforced.
- Event idempotency must not be bypassed.

Best next improvement:

- Fix fixture/test portability first, then regenerate OpenAPI from the current route surface and artifact shapes.
