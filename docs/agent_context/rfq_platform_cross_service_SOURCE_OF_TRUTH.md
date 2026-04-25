# RFQ Platform — Cross-Service Source of Truth for AI Agents

## 1. Purpose of This Document

This document is the canonical cross-service context for future AI coding agents working across `rfq_manager_ms`, `rfq_intelligence_ms`, and `rfq_ui_ms`. It explains the communication contracts, ownership boundaries, integration seams, known gaps, and rules that must be preserved when changes touch more than one service.

Sources used, in priority order:

- `microservices/rfq_manager_ms/docs/agent_context/rfq_manager_ms_SOURCE_OF_TRUTH.md`
- `microservices/rfq_intelligence_ms/docs/agent_context/rfq_intelligence_ms_SOURCE_OF_TRUTH.md`
- `frontend/rfq_ui_ms/docs/agent_context/rfq_ui_ms_SOURCE_OF_TRUTH.md`
- Actual routes, connectors, models, settings, tests, Docker files, and environment examples in all three repositories.

If this document conflicts with implementation code, the code wins and this file must be updated.

## 2. One-Paragraph Platform Summary

The RFQ platform is split into three services with separate truth boundaries: `rfq_manager_ms` is the operational lifecycle backbone for RFQs, workflows, stages, files, subtasks, reminders, stats, and analytics; `rfq_intelligence_ms` produces deterministic derived intelligence artifacts from manager RFQ context, stage files, workbooks, source packages, and event-like triggers; `rfq_ui_ms` is the Next.js frontend that renders dashboards, RFQ lists/details, operational workspaces, reminders, and intelligence panels by calling the two backend APIs or, in explicit mock mode, local demo data.

## 3. Service Responsibility Map

| Service | Primary Role | Owns | Does Not Own | Main Consumers | Main Dependencies |
| --- | --- | --- | --- | --- | --- |
| `rfq_manager_ms` | Operational RFQ lifecycle source of truth | RFQ identity, metadata, status, workflow templates, instantiated stages, current stage, stage progression, subtasks, notes, stage file metadata/storage, reminders, reminder rules, operational stats/analytics/export, health/metrics | Workbook parsing, MR package parsing, intelligence artifacts, chatbot reasoning, frontend rendering | `rfq_ui_ms`, `rfq_intelligence_ms`, future services | PostgreSQL, file storage path, IAM seam, event bus seam |
| `rfq_intelligence_ms` | Deterministic derived intelligence layer | Intake profiles, intelligence briefings, package parse artifacts, workbook parse artifacts, parser reports, workbook review reports, snapshots/read models, analytical records, parser issues/warnings, cross-check outputs | RFQ lifecycle state, RFQ status truth, workflow progression, current stage truth, frontend behavior, chatbot answer generation | `rfq_ui_ms`, future automation/jobs | PostgreSQL, `rfq_manager_ms` read connector, manager upload mount/local fixtures, event-like payloads |
| `rfq_ui_ms` | Frontend experience and presentation layer | Pages, navigation, dashboards, RFQ list/detail views, role-based UI visibility, API clients, loading/error/empty states, upload interactions, mock/demo mode, visual design/theme | Operational lifecycle truth, intelligence truth, backend permission enforcement, parser logic, database persistence, fake success states | Human users | `rfq_manager_ms` API, `rfq_intelligence_ms` API, browser env vars, mock data |

## 4. Source-of-Truth Matrix

| Domain / Data | Source of Truth | Consumers | Must Not Be Duplicated In | Notes |
| --- | --- | --- | --- | --- |
| RFQ identity | `rfq_manager_ms` | UI, intelligence | UI mock logic, intelligence DB as independent primary identity | Manager `rfq.id` is UUID primary key; `rfq_code` is display/business code. |
| RFQ metadata | `rfq_manager_ms` | UI, intelligence connector | UI local state, intelligence artifacts except as snapshots/derived references | Intelligence may copy selected metadata into artifacts as derived evidence. |
| RFQ status | `rfq_manager_ms` | UI | Intelligence, UI mock/derived state | Terminal/status transitions belong to manager. |
| Workflow templates | `rfq_manager_ms` | UI create form/workflow screens | UI hardcoded lifecycle rules | UI may render templates but must not define operational rules. |
| RFQ stages | `rfq_manager_ms` | UI, intelligence connector | Intelligence lifecycle logic, UI local simulators | Manager instantiates stages from workflow templates. |
| Current stage | `rfq_manager_ms` | UI | UI-derived stage selection as truth, intelligence artifacts | UI can highlight current stage from backend fields only. |
| Stage progress | `rfq_manager_ms` | UI | UI business rules | UI displays progress; it must not own progression rules. |
| Blockers | `rfq_manager_ms` if implemented | UI | Intelligence, UI-only state | UI has blocker display/tests, but backend truth is manager. |
| Subtasks | `rfq_manager_ms` | UI | Intelligence, UI-only stores | CRUD is manager-backed in live mode. |
| Stage notes | `rfq_manager_ms` | UI | Intelligence, UI-only stores | Manager exposes note creation on stage detail. |
| Stage files | `rfq_manager_ms` | UI, intelligence connector | Intelligence as operational file owner | Manager stores uploaded file metadata and paths. Intelligence may read source/workbook files by reference. |
| Reminders | `rfq_manager_ms` | UI | Intelligence, UI-only timers | Reminder rules and statuses belong to manager. |
| Stats/KPIs | `rfq_manager_ms` | UI dashboard | UI hardcoded KPIs as truth | UI mock KPIs must stay aligned with manager shape. |
| Analytics | `rfq_manager_ms` | UI overview/dashboard | UI local aggregation as truth | UI consumes manager analytics in live mode. |
| Intake profile | `rfq_intelligence_ms` | UI intelligence panels | Manager, UI mock as truth | Created from event/trigger and manager context. |
| MR package structure | `rfq_intelligence_ms` | UI intelligence panels | Manager, UI local parsing | Implemented through package parser modules. |
| Workbook profile | `rfq_intelligence_ms` | UI intelligence panels | Manager, UI local parsing | Created from workbook parsing flow. |
| Cost breakdown profile | `rfq_intelligence_ms` | UI artifact catalog/snapshot | UI calculations | Artifact type exists; UI has no dedicated cost breakdown endpoint beyond catalog/snapshot consumption. |
| Parser report | `rfq_intelligence_ms` | UI artifact catalog/snapshot | UI fake reports | Parser issues/warnings must be preserved. |
| Workbook review report | `rfq_intelligence_ms` | UI intelligence panel | UI local comparison | Derived by intelligence from workbook/package/intake data. |
| Snapshot/read model | `rfq_intelligence_ms` | UI RFQ detail intelligence section | Manager, UI local cache as truth | Snapshot freshness semantics are partially implicit. |
| Role/user context | UI presentation and manager auth seam | UI, manager | UI as security authority | UI role switching is presentation-level. Manager auth/IAM is authoritative where enabled. |
| UI navigation | `rfq_ui_ms` | Users | Backends | Backends expose APIs only. |
| Mock data | `rfq_ui_ms` mock layer | UI in explicit mock mode | Backends, live-mode code paths | Mock data is not proof of backend behavior. |
| File upload interactions | `rfq_ui_ms` interaction, `rfq_manager_ms` persistence | Users, intelligence connector | UI as file owner | Current UI uploads stage files to manager; intelligence reads manager file references or uses manual triggers. |

## 5. High-Level Communication Map

Implemented communication:

```text
rfq_ui_ms
  -> calls rfq_manager_ms for RFQ lifecycle, workflow, stage, subtask, file, reminder, stats, analytics, and health data
  -> calls rfq_intelligence_ms for snapshots, briefings, workbook profiles, workbook reviews, artifact catalogs, manual trigger/reprocess actions, and health data

rfq_intelligence_ms
  -> calls rfq_manager_ms through a read-only ManagerConnector for RFQ detail, RFQ stages, stage detail, and file references
  -> resolves manager-uploaded files through MANAGER_UPLOADS_MOUNT_PATH, direct path checks, or LOCAL_FIXTURES_DIR
  -> processes event-like envelopes through explicit route triggers and internal event processing

rfq_manager_ms
  -> exposes operational APIs under /rfq-manager/v1 plus /health and /metrics
  -> publishes best-effort lifecycle events through an event bus connector seam when configured
  -> does not call rfq_intelligence_ms directly
```

Expected but not fully implemented communication:

- Manager has an event bus seam and publishes lifecycle events such as `rfq.created`, `rfq.deadline_changed`, `rfq.status_changed`, and `stage.advanced`.
- Intelligence has event handlers for `rfq.created`, `workbook.uploaded`, and `outcome.recorded`, but no confirmed durable event bus consumer.
- UI has manual trigger actions that call intelligence trigger endpoints. This is the current practical bridge for some intelligence workflows.
- Manager stage file upload does not confirmably publish `workbook.uploaded`, and manager terminal outcome does not confirmably publish `outcome.recorded`.

## 6. Runtime Configuration Map

| Variable | Repo | Purpose | Required? | Example / Pattern | Risk |
| --- | --- | --- | --- | --- | --- |
| `DATABASE_URL` | manager | Manager PostgreSQL connection | Required for real persistence | `postgresql+psycopg2://.../rfq_manager_db` | Do not commit secrets. |
| `APP_ENV` | manager | Runtime environment label | Optional | `development` | Must align with auth bypass expectations. |
| `APP_DEBUG` | manager | Debug mode flag | Optional | `true` | Debug behavior must not leak to production. |
| `APP_PORT` | manager | App port setting | Optional | `8000` | Uvicorn command may override. |
| `IAM_SERVICE_URL` | manager | IAM service seam | Optional/seam | `http://localhost:8001/iam/v1` | Port can conflict conceptually with intelligence default if not isolated by context. |
| `JWT_SECRET` | manager | JWT secret/config placeholder | Required if JWT auth path is active | Never expose | Secret must not be committed. |
| `AUTH_BYPASS_ENABLED` | manager | Enables local/dev auth bypass | Optional | `false` | Dangerous outside local use. |
| `AUTH_BYPASS_USER_ID` | manager | Bypass actor id | Optional | `v1-demo-user` | Dev-only identity. |
| `AUTH_BYPASS_USER_NAME` | manager | Bypass actor name | Optional | `System` | Dev-only identity. |
| `AUTH_BYPASS_TEAM` | manager | Bypass actor team | Optional | `workspace` | Dev-only identity. |
| `AUTH_BYPASS_PERMISSIONS` | manager | CSV bypass permissions | Optional | `rfq:*,workflow:*,...` | Powerful; not listed in manager `.env.example` but used in code. |
| `AUTH_BYPASS_DEBUG_HEADERS_ENABLED` | manager | Allows debug actor headers in bypass mode | Optional | `false` | Must remain disabled outside debugging. |
| `IAM_REQUEST_TIMEOUT_SECONDS` | manager | IAM connector timeout | Optional | `3.0` | IAM seam only. |
| `EVENT_BUS_URL` | manager | Event bus connector URL | Optional/seam | `http://localhost:8002/events/v1` | Best-effort event delivery; no confirmed consumer path. |
| `EVENT_BUS_REQUEST_TIMEOUT_SECONDS` | manager | Event bus timeout | Optional | `3.0` | Failed publishes should not corrupt manager state. |
| `FILE_STORAGE_PATH` | manager | Stage file storage root | Optional | `./uploads` | Intelligence needs access/mount mapping to read files. |
| `MAX_FILE_SIZE_MB` | manager | Stage upload size limit | Optional default `50` | `50` | Missing from `.env.example`; upload behavior depends on it. |
| `CORS_ORIGINS` | manager | Allowed browser origins | Optional | `http://localhost:3000,http://localhost:5173` | Must include UI origin in real mode. |
| `APP_NAME` | intelligence | App name | Optional | `rfq_intelligence_ms` | Low risk. |
| `APP_PORT` | intelligence | App port | Optional | `8001` | Must differ from manager when co-running. |
| `ENVIRONMENT` | intelligence | Runtime environment label | Optional | `local` | Low risk. |
| `APP_DEBUG` | intelligence | Debug flag | Optional | `false` | Avoid production debug leakage. |
| `CORS_ORIGINS` | intelligence | Allowed browser origins | Optional | `*` | Wide-open default is convenient but broad. |
| `DATABASE_URL` | intelligence | Intelligence PostgreSQL connection | Required for real persistence | `postgresql+psycopg2://.../rfq_intelligence_db` | Do not commit secrets. |
| `MANAGER_MS_BASE_URL` | intelligence | Base URL for manager connector | Required for manager integration | `http://localhost:18000` in `.env.example` | Differs from UI default manager URL `http://localhost:8000`; scenario/local setup must be explicit. |
| `MANAGER_REQUEST_TIMEOUT_SECONDS` | intelligence | Manager connector timeout | Optional default `10.0` | `10.0` | Used in code but missing from `.env.example`. |
| `MANAGER_UPLOADS_MOUNT_PATH` | intelligence | Mounted manager upload directory | Optional default `/app/manager_uploads` | `/app/manager_uploads` | Required for parsing files stored by manager in containerized flows. |
| `LOCAL_FIXTURES_DIR` | intelligence | Local fallback fixture root | Optional | Local path | Used via `os.getenv`; not in Pydantic settings or `.env.example`. |
| `NEXT_PUBLIC_USE_MOCK_DATA` | UI | Selects mock mode vs live API mode | Optional | `true` or `false` | Mock mode can hide integration issues. |
| `NEXT_PUBLIC_MANAGER_API_URL` | UI | Manager API origin/base URL | Required for live manager calls | `http://localhost:8000` | Must point to manager origin, not include `/rfq-manager/v1`. |
| `NEXT_PUBLIC_INTELLIGENCE_API_URL` | UI | Intelligence API origin/base URL | Required for live intelligence calls | `http://localhost:8001` | Must point to intelligence origin, not include `/intelligence/v1`. |
| `NEXT_PUBLIC_DEMO_LATENCY_MS` | UI | Mock/demo latency | Optional | `650` | Mock-only. |
| `NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED` | UI | Enables debug auth headers for manager calls | Optional | `true` | Used in code but missing from UI `.env.example`; debug-only. |
| `NEXT_PUBLIC_MANAGER_API_TOKEN` | UI | Browser-visible bearer token for manager calls | Optional | Do not use real secrets | `NEXT_PUBLIC` exposes it to the browser; not safe for production secrets. |

## 7. API Consumption Matrix

### Dashboard / KPIs

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Manager dashboard metrics | `src/connectors/manager/index.ts` / `getDashboardMetrics` | manager | `/rfq-manager/v1/rfqs/stats` | GET | Operational KPI/stat object | Real or mock equivalent | Mock KPI shape can drift. |
| Manager dashboard analytics | `src/connectors/manager/index.ts` / `getDashboardAnalytics` | manager | `/rfq-manager/v1/rfqs/analytics` | GET | Analytics groupings/trends | Real or mock equivalent | UI aggregation must not replace backend analytics truth. |
| Executive dashboard RFQ list | `src/hooks/useDashboardData.ts` via manager list calls | manager | `/rfq-manager/v1/rfqs` | GET | RFQ list page data | Real or mock equivalent | Executive notes may be local presentation, not backend truth. |

### RFQ List

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RFQ list/search/filter | `src/connectors/manager/index.ts` / `listRfqs` | manager | `/rfq-manager/v1/rfqs` | GET | Paginated/list RFQ summaries | Real or mock equivalent | Query params and response wrappers must stay aligned. |

### RFQ Detail

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RFQ detail | `getRfqDetail` | manager | `/rfq-manager/v1/rfqs/{rfqId}` | GET | RFQ metadata/detail | Real or mock equivalent | `rfqId` must be manager UUID in live mode. |
| RFQ stages for detail | `getRfqDetail`, `getRfqStages` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages` | GET | Stage list | Real or mock equivalent | UI must use backend current-stage markers/ids. |
| Current stage detail | `getRfqDetail`, `getStageDetail` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}` | GET | Stage detail with notes/files/subtasks if exposed | Real or mock equivalent | Additional detail calls may fail if ids are stale. |

### Create RFQ

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Create RFQ form submit | `createRfq` | manager | `/rfq-manager/v1/rfqs` | POST | Created RFQ response | Real or mock equivalent | UI must not locally instantiate workflow stages. |

### Workflow Selection

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Workflow catalog | `listWorkflows` | manager | `/rfq-manager/v1/workflows` and `/workflows/{workflowId}` | GET | Workflow summaries/details | Real or mock equivalent | UI test path drift exists around workflow catalog truth. |
| Workflow detail/stages | `getWorkflow`, `getWorkflowStages` | manager | `/rfq-manager/v1/workflows/{workflowId}` | GET | Workflow template and stage templates | Real or mock equivalent | Must remain manager-defined. |

### Stage Timeline and Stage Advance

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage update | `updateStage` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}` | PATCH | Updated stage | Real or mock equivalent | UI must not allow lifecycle bypass through metadata patching. |
| Stage advance | `advanceStage` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/advance` | POST | Advanced stage/RFQ progress response | Real or mock equivalent | Backend rejects invalid/out-of-order transitions; UI must surface errors. |
| Stage note add | `addStageNote` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/notes` | POST | Note response/stage detail update | Real or mock equivalent | Notes are manager-owned. |

### Subtasks

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Create subtask | `createSubtask` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/subtasks` | POST | Subtask | Real or mock equivalent | UI role hiding is not security. |
| Update subtask | `updateSubtask` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/subtasks/{subtaskId}` | PATCH | Subtask | Real or mock equivalent | Must refresh stage/detail data after mutation. |
| Delete subtask | `deleteSubtask` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/subtasks/{subtaskId}` | DELETE | Delete result/no content | Real or mock equivalent | Backend is source of deletion truth. |

### Files

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage file upload | `uploadStageFile` | manager | `/rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/files` | POST multipart | Stage file metadata | Real or mock equivalent | Upload target is operational stage file storage, not direct intelligence upload. |
| Stage file delete | `deleteStageFile` | manager | `/rfq-manager/v1/files/{fileId}` | DELETE | Delete result/no content | Real or mock equivalent | File delete semantics must match manager persistence/storage behavior. |
| File download link display | UI consumes file `download_url` | manager | `/rfq-manager/v1/files/{fileId}/download` if URL returned | GET | File bytes | URL-based | Direct frontend function for download endpoint was not confirmed. |

### Reminders

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Reminder list | reminder connector functions | manager | `/rfq-manager/v1/reminders` | GET | Reminder list | Real or mock equivalent | Reminder status shape must stay aligned. |
| Reminder stats | reminder connector functions | manager | `/rfq-manager/v1/reminders/stats` | GET | Reminder KPIs | Real or mock equivalent | UI must not compute rule truth locally. |
| Reminder rules | reminder connector functions | manager | `/rfq-manager/v1/reminders/rules` | GET | Reminder rules | Real or mock equivalent | Rule changes belong to manager. |
| Create/resolve/process/test reminders | reminder connector functions | manager | `/reminders`, `/reminders/{id}/resolve`, `/reminders/process`, `/reminders/test` | POST | Reminder mutation/test/process responses | Real or mock equivalent | Outbound delivery is a stub/service seam. |
| Update reminder rule | reminder connector functions | manager | `/rfq-manager/v1/reminders/rules/{ruleId}` | PATCH | Reminder rule | Real or mock equivalent | Rule enablement affects backend behavior. |

### Analytics

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Overview analytics | `useOverviewData`, manager analytics connector | manager | `/rfq-manager/v1/rfqs/analytics` | GET | Operational analytics | Real or mock equivalent | No confirmed intelligence enrichment in this path. |

### Intelligence Briefing and Artifacts

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Intelligence snapshot | `src/connectors/intelligence/index.ts` / `getSnapshot` | intelligence | `/intelligence/v1/rfqs/{rfqId}/snapshot` | GET | Snapshot/read model | Real or mock equivalent | Snapshot freshness is not strongly visible in UI contract. |
| Briefing | `getBriefing` | intelligence | `/intelligence/v1/rfqs/{rfqId}/briefing` | GET | Intelligence briefing | Real or mock equivalent | Missing artifact must render as missing, not fake readiness. |
| Workbook profile | `getWorkbookProfile` | intelligence | `/intelligence/v1/rfqs/{rfqId}/workbook-profile` | GET | Workbook profile artifact | Real or mock equivalent | Depends on manager file references and parser availability. |
| Workbook review | `getWorkbookReview` | intelligence | `/intelligence/v1/rfqs/{rfqId}/workbook-review` | GET | Workbook review report | Real or mock equivalent | Must preserve issue/warning semantics. |
| Artifact catalog | `getArtifactCatalog` | intelligence | `/intelligence/v1/rfqs/{rfqId}/artifacts` | GET | Available artifact catalog | Real or mock equivalent | Dedicated endpoints do not exist for every artifact type. |
| Reprocess artifact | `requestArtifactReprocess` | intelligence | `/intelligence/v1/rfqs/{rfqId}/reprocess/{kind}` | POST | Reprocess response | Real or mock equivalent | Only `intake` and `workbook` kinds are confirmed. |
| Manual intake/workbook/outcome triggers | trigger functions | intelligence | `/trigger/intake`, `/trigger/workbook`, `/trigger/outcome` | POST | Trigger processing response | Real or mock equivalent | Manual trigger currently compensates for missing event bus consumer. |

### Health Checks

| Frontend Feature | Frontend File / Function | Backend Service | Backend Endpoint | Method | Data Returned | Real/Mock | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Backend connection status | `ConnectionProvider` | manager | `/health` | GET | Health status | Real mode only; mock mode fakes connected | Mock mode can hide backend downtime. |
| Backend connection status | `ConnectionProvider` | intelligence | `/health` | GET | Health status | Real mode only; mock mode fakes connected | Mock mode can hide backend downtime. |

Export is implemented by manager at `/rfq-manager/v1/rfqs/export`, but no frontend consumer was confirmed.

## 8. Backend Contract Alignment

| Contract Area | Frontend Type/File | Backend Source/File | Match Status | Drift Risk | Suggested Fix |
| --- | --- | --- | --- | --- | --- |
| RFQ summary/list item | UI manager connector/types | Manager RFQ response schemas/translators | Partially aligned | Mock/demo ids may be code-shaped while live ids are UUIDs. | Add contract tests against manager OpenAPI/live fixture. |
| RFQ detail | UI RFQ detail types/hooks | Manager RFQ detail response and stage fetches | Partially aligned | UI composes detail from multiple manager calls; changes in stage detail shape can break panels. | Snapshot UI contract fixture from live manager route. |
| Workflow | UI workflow types/connectors | Manager workflow routes/models | Partially aligned | UI truth-gate test expected path drift was found in previous UI validation. | Fix path assumptions and compare to manager route output. |
| Stage | UI stage/timeline/workspace types | Manager RFQ stage schemas/controllers | Partially aligned | Progress/current-stage display can drift if UI derives too much. | Keep current stage and transition results backend-driven. |
| Subtask | UI operational workspace types | Manager subtask routes/schemas | Partially aligned | Status/priority enum drift possible. | Add manager fixture-backed UI type test. |
| File | UI stage file types | Manager file/stage file routes | Partially aligned | Upload is manager-owned but intelligence also needs file references; storage path accessibility is external. | Test stage upload then intelligence workbook trigger end to end. |
| Reminder | UI reminder connector/types | Manager reminder routes/schemas | Partially aligned | Reminder rule/status evolution can break reminder center. | Add response contract test for list/stats/rules. |
| Stats | UI dashboard metrics types | Manager stats route | Partially aligned | Mock KPIs may include fields backend does not return or vice versa. | Generate mock from backend fixture or validate shape. |
| Analytics | UI overview/dashboard analytics types | Manager analytics route | Partially aligned | UI may render assumptions about grouping keys. | Add schema test for analytics groups. |
| Intelligence artifact catalog | UI intelligence types | Intelligence artifact routes/models | Partially aligned | UI has generic catalog but not dedicated retrieval for every artifact type. | Keep catalog generic and add typed panels only with backend route support. |
| Briefing | UI intelligence connector/types | Intelligence briefing endpoint | Partially aligned | Missing briefing must not become fabricated text. | Explicit empty/missing state tests. |
| Workbook report/review | UI intelligence connector/types | Intelligence workbook profile/review endpoints | Partially aligned | Parser issue taxonomy changes could break display. | Add fixture tests with warnings/errors. |
| Snapshot | UI intelligence connector/types | Intelligence snapshot endpoint/service | Partially aligned | Freshness semantics are not strongly enforced cross-service. | Add `generated_at`/source status display tests if fields exist. |

## 9. RFQ Identity and Reference Flow

Manager is the identity authority. In manager code, `rfq.id` is a UUID primary key and `rfq_code` is a unique display/business code. UI route parameters in live mode must use manager `id`, not `rfq_code`. Intelligence stores and retrieves artifacts by `rfq_id` and uses manager connector calls with that `rfq_id`.

| Usage | Service | Field | Source | Risk | Rule |
| --- | --- | --- | --- | --- | --- |
| Database identity | manager | `id` / `rfq_id` | Manager ORM/model | Low if treated as UUID | Use this for API path identity and persistence references. |
| Display/business code | manager/UI | `rfq_code` / `rfqCode` | Manager generated field | Medium if used as route id | Do not use `rfq_code` as database identity unless code explicitly does. |
| Frontend route param | UI | `rfqId` | Link from RFQ list/card/detail | Medium in mock mode because demo ids may look like RFQ codes | In live mode pass manager UUID. |
| Intelligence artifact linkage | intelligence | `rfq_id` | Trigger payload or route path | Medium if UI sends code-shaped id | Do not create intelligence artifacts without a clear manager RFQ reference. |
| Manager file linkage | manager/intelligence | `rfq_id`, `stage_id`, `file_id`, `storage_reference` | Manager stage file upload | Medium if storage mount is missing | Intelligence should resolve files through manager context and configured mounts. |
| Event payload identity | manager/intelligence | `payload.rfq_id`; sometimes `rfq_code` in manager publish payloads | Event envelopes/triggers | Medium because event bus path is incomplete | Event contracts must state whether `rfq_id` is UUID and include `rfq_code` only as display/context. |

Strict identity rules:

- Do not use `rfq_code` as database identity unless implementation explicitly does.
- Do not use `rfq_id` as display identity unless the UI intentionally wants a technical id.
- Do not create intelligence artifacts without a manager RFQ reference.
- Do not mix mock code-shaped ids with live UUID ids in the same runtime path.

## 10. File Upload and Artifact Flow

Implemented operational file flow:

```text
User
-> rfq_ui_ms operational workspace upload control
-> rfq_manager_ms POST /rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/files
-> manager validates file size/type, writes file below FILE_STORAGE_PATH, stores stage file metadata
-> UI refreshes/uses manager stage file metadata and download URL
```

Implemented intelligence file reference flow:

```text
UI manual intelligence trigger or intelligence intake route
-> rfq_intelligence_ms
-> ManagerConnector reads manager RFQ/stage/stage file context
-> connector identifies source packages and workbooks from manager file type metadata
-> connector resolves storage_reference/file_path through MANAGER_UPLOADS_MOUNT_PATH, direct path checks, or LOCAL_FIXTURES_DIR
-> parser/artifact services generate intelligence artifacts
-> UI retrieves snapshot/briefing/workbook/review/artifact catalog
```

Current limitations:

- The UI upload path is manager stage file upload, not a direct intelligence upload.
- No confirmed UI flow uploads a workbook directly to `rfq_intelligence_ms`.
- Manager upload does not confirmably emit `workbook.uploaded`.
- Intelligence can parse workbook/package inputs when it can resolve manager file references, but the cross-service trigger is manual or route-driven rather than a confirmed event bus consumer.
- File storage access is operationally fragile unless manager uploads are mounted into the intelligence container/path expected by `MANAGER_UPLOADS_MOUNT_PATH`.

## 11. Event and Trigger Flow

| Event / Trigger | Producer | Consumer | Implementation Status | Payload Fields | Risk | Suggested Fix |
| --- | --- | --- | --- | --- | --- | --- |
| `rfq.created` | manager event bus seam; intelligence manual trigger | Intelligence lifecycle handler | Stubbed/partially implemented | Manager publish includes `rfq_id`, `rfq_code`, metadata/deadline; intelligence manual trigger sends `{rfq_id}` envelope | No confirmed durable bus consumer; manual trigger may be required. | Define one shared event contract and wire a real consumer or documented synchronous trigger. |
| `rfq.deadline_changed` | manager | Could not confirm consumer | Expected but missing consumer | `rfq_id`, deadline fields if published | Intelligence/UI may not react to deadline changes. | Either add consumer or document as manager-only operational event. |
| `rfq.status_changed` | manager | Could not confirm consumer | Expected but missing consumer | `rfq_id`, status fields if published | Intelligence `outcome.recorded` is separate and not automatically produced by manager. | Map terminal status changes to outcome events only if business requires it. |
| `stage.advanced` | manager | Could not confirm consumer | Expected but missing consumer | stage/RFQ transition fields if published | UI relies on refetch, not events. | Add integration tests if future consumers appear. |
| `workbook.uploaded` | Intelligence manual trigger envelope; expected from upload flow | Intelligence workbook handler | Stubbed/manual | `{rfq_id, workbook_ref, workbook_filename, uploaded_at}` | Manager upload does not confirmably emit this event. | Publish from manager upload when file type is workbook, or keep explicit UI trigger with clear UX. |
| `outcome.recorded` | Intelligence manual trigger envelope | Intelligence outcome handler | Stubbed/manual | `{rfq_id, outcome, recorded_at, outcome_reason}` | Manager terminal outcome is not automatically linked. | Define outcome source and contract before learning/enrichment work. |
| UI health polling | UI `ConnectionProvider` | Manager/intelligence `/health` | Implemented | No domain payload | In mock mode health is faked connected. | Keep live connection status distinct from mock status. |

## 12. Mock Data vs Real Backend Behavior

Mock mode is enabled by `NEXT_PUBLIC_USE_MOCK_DATA=true`. In mock mode, UI connectors use local/demo data and connection status is treated as connected without real health checks. Real API mode is enabled by setting `NEXT_PUBLIC_USE_MOCK_DATA=false` and configuring `NEXT_PUBLIC_MANAGER_API_URL` and `NEXT_PUBLIC_INTELLIGENCE_API_URL`.

| UI Feature | Mock Source | Real API Source | Shape Match | Drift Risk | Action Needed |
| --- | --- | --- | --- | --- | --- |
| Dashboard KPIs | UI mock/demo data | Manager `/rfqs/stats`, `/rfqs/analytics` | Partially aligned | Mock fields can drift from backend schema. | Validate mock objects against connector output types. |
| RFQ list | UI mock RFQ summaries | Manager `/rfqs` | Partially aligned | Mock ids may be RFQ-code-like while live ids are UUIDs. | Keep separate `id` and `rfqCode` in all UI paths. |
| RFQ detail | UI mock detail/stages | Manager detail + stages endpoints | Partially aligned | Mock may include richer fields than backend or omit backend errors. | Add live fixture tests. |
| Workflow catalog | UI mock workflow data | Manager workflow endpoints | Partially aligned | Existing UI truth-gate path assumption drift. | Fix test path and compare to manager fixtures. |
| Stage workspace | UI mock stage/subtask/file data | Manager stage/subtask/file routes | Partially aligned | Mock may allow state transitions backend rejects. | Keep mutations backend-driven in live mode and surface rejections. |
| Reminders | UI mock reminders/rules/stats | Manager reminder endpoints | Partially aligned | Rule/status drift possible. | Add response schema tests. |
| Intelligence panels | UI mock intelligence artifacts | Intelligence snapshot/briefing/workbook/review/artifacts | Partially aligned | Mock readiness can imply intelligence exists when backend artifacts are missing. | Test missing-artifact empty states. |
| Health status | UI mock connected status | `/health` on both backends | Mismatched by design | Mock mode hides backend failures. | Label/handle mock connectivity separately from live connectivity. |

## 13. Role and Permission Alignment

UI roles are presentation-level. Manager has auth/IAM seams, permission dependencies, and local bypass/debug-header behavior. Intelligence has no confirmed auth/IAM enforcement in the generated service source-of-truth. UI role hiding must never be treated as backend security.

| Role / Permission | UI Behavior | Manager Enforcement | Intelligence Enforcement | Alignment | Risk |
| --- | --- | --- | --- | --- | --- |
| Executive | Dashboard/portfolio/read-focused behavior in UI | Backend permission model may still allow/deny independently | Could not confirm | Partially aligned | UI may show read-only experience while backend permissions are not role-mapped. |
| Estimation Manager | Operational owner UI with create/manage/progress actions where shown | Manager permissions enforced when auth active or bypass configured | Could not confirm | Partially aligned | UI action visibility does not prove backend authorization. |
| Estimator | Scoped contributor UI behavior where implemented | Manager permissions authoritative when active | Could not confirm | Partially aligned | UI may hide/show actions differently from backend policy. |
| Debug actor headers | UI can send `X-Debug-*` only when env flag enabled | Manager honors only with bypass/debug header flag | Not applicable | Aligned for dev seam | Dangerous if enabled outside local debugging. |
| Bearer token | UI can send `NEXT_PUBLIC_MANAGER_API_TOKEN` | Manager may validate via auth seam | Not implemented for intelligence | Weak | Public env token is visible in browser; do not store real secrets. |

## 14. Cross-Service Workflows

### 14.1 Dashboard Load

```text
Dashboard route/page
-> UI hook/service
-> manager GET /rfq-manager/v1/rfqs/stats
-> manager GET /rfq-manager/v1/rfqs/analytics
-> optionally manager GET /rfq-manager/v1/rfqs for portfolio rows
-> UI renders cards/charts/tables with role-specific presentation
```

No confirmed intelligence data is required for dashboard load. In mock mode, dashboard data comes from local/demo data.

### 14.2 RFQ List and Search

```text
RFQ list page
-> UI list hook
-> manager GET /rfq-manager/v1/rfqs with page/size/search/sort/status filters
-> UI renders list/cards/table and links to /rfqs/{rfqId}
```

Manager owns filtering, pagination, and RFQ identity in live mode. UI must not use `rfq_code` as a route identity unless the backend explicitly supports that path.

### 14.3 RFQ Detail Load

```text
RFQ detail page
-> manager GET /rfq-manager/v1/rfqs/{rfqId}
-> manager GET /rfq-manager/v1/rfqs/{rfqId}/stages
-> manager GET /rfq-manager/v1/rfqs/{rfqId}/stages/{currentStageId} when needed
-> intelligence GET /intelligence/v1/rfqs/{rfqId}/snapshot
-> intelligence GET /intelligence/v1/rfqs/{rfqId}/briefing
-> intelligence GET /intelligence/v1/rfqs/{rfqId}/workbook-profile
-> intelligence GET /intelligence/v1/rfqs/{rfqId}/workbook-review
-> intelligence GET /intelligence/v1/rfqs/{rfqId}/artifacts
-> UI renders operational and intelligence panels
```

Operational sections must render manager truth. Intelligence sections must show missing/error states honestly when artifacts are absent.

### 14.4 RFQ Creation

```text
Create RFQ page/form
-> UI validates form fields for usability
-> manager POST /rfq-manager/v1/rfqs
-> manager selects workflow, creates RFQ, instantiates stages, sets current_stage_id
-> manager may publish best-effort rfq.created event
-> UI redirects/refetches using created RFQ id
-> intelligence is not automatically confirmed to run unless a trigger/event consumer is wired
```

UI must not create stage instances locally. Intelligence intake may require explicit trigger until event integration is completed.

### 14.5 Stage Advancement

```text
Stage action in UI
-> manager POST /rfq-manager/v1/rfqs/{rfqId}/stages/{stageId}/advance
-> manager validates current stage, transition rules, blockers/required fields where implemented
-> manager updates stage/RFQ progress/current_stage_id
-> manager may publish stage.advanced event
-> UI refetches manager RFQ/stage data
```

No confirmed intelligence side effect is attached to stage advancement.

### 14.6 Workbook Upload and Review

Implemented pieces:

```text
UI stage file upload
-> manager stage file endpoint
-> manager persists workbook-like file metadata if file type is "Estimation Workbook"
-> UI or user can trigger intelligence workbook processing
-> intelligence ManagerConnector finds workbook stage file reference
-> intelligence workbook parser generates workbook artifacts/review
-> UI reads workbook profile/review/artifact catalog
```

Missing or unclear pieces:

- No confirmed direct intelligence upload endpoint used by UI for persisted workbook artifacts.
- No confirmed automatic `workbook.uploaded` event from manager upload to intelligence handler.
- File path sharing between manager and intelligence depends on deployment/mount configuration.

### 14.7 MR Package Intake

Implemented pieces:

```text
Manager stage file metadata can mark source package/client RFQ files
-> intelligence ManagerConnector resolves source package references
-> package parser modules can scan ZIP/folder structures and produce package/intake artifacts
-> intelligence briefing/snapshot routes expose derived outputs
-> UI intelligence panels consume the resulting artifact routes
```

The package parser exists in intelligence tests/modules, but a fully automatic upload-to-parse event flow from manager to intelligence was not confirmed.

### 14.8 Reminder Flow

```text
Reminder center or operational panel
-> UI reminder connector
-> manager /rfq-manager/v1/reminders* endpoints
-> manager reminder controller/rules/services update reminder state or process/test reminders
-> UI refreshes reminder list/stats/rules
```

Intelligence is not part of the reminder flow.

### 14.9 Analytics Flow

```text
Overview/dashboard UI
-> manager GET /rfq-manager/v1/rfqs/analytics
-> manager datasource/controller computes operational analytics
-> UI renders charts/tables
```

No confirmed intelligence enrichment of analytics exists. Do not mix intelligence-derived conclusions into manager analytics without an explicit contract.

## 15. Cross-Service Invariants

- Manager remains the source of operational RFQ truth.
- Intelligence remains the source of derived intelligence artifact truth.
- UI never invents backend truth in live mode.
- UI mock data must stay aligned with backend contracts and remain clearly separated from real API mode.
- `rfq_id`/`rfq_code` usage must remain consistent: UUID ids for backend identity, codes for display.
- Manager lifecycle changes must be reflected in UI types, mock data, and tests.
- Intelligence artifact schema changes must be reflected in UI types, display components, and tests.
- Backend API changes must update frontend clients, mocks, docs, and contract tests.
- Frontend role visibility must not be treated as security.
- File upload target must be clear: operational stage file versus intelligence input.
- Events/triggers must have stable payload contracts before cross-service automation depends on them.
- Missing intelligence data must display as missing, not fake content.
- Backend errors must be surfaced honestly; UI must not replace failures with fake success.
- Manager events must remain best-effort unless durable delivery and consumers are implemented and tested.
- Intelligence must not mutate manager lifecycle state directly.
- Other services must not write directly to manager or intelligence databases.

## 16. Cross-Service Gaps and Risks

| Gap / Risk | Affected Services | Severity | Evidence | Impact | Suggested Fix |
| --- | --- | --- | --- | --- | --- |
| Event producer/consumer mismatch | manager, intelligence, UI | Important but non-blocking | Manager publishes `rfq.created`, `rfq.deadline_changed`, `rfq.status_changed`, `stage.advanced`; intelligence handles `rfq.created`, `workbook.uploaded`, `outcome.recorded`; no durable bus consumer confirmed. | Intelligence may not update automatically after lifecycle/file/outcome changes. | Define shared event contract and wire a tested consumer or keep explicit synchronous triggers. |
| Workbook upload does not automatically trigger workbook parsing | manager, intelligence, UI | Important but non-blocking | UI uploads files to manager; intelligence has manual workbook trigger and handler. | Users may expect artifacts after upload but need manual trigger/refetch. | Emit/consume `workbook.uploaded` or make UI trigger explicit and documented. |
| File storage mount coupling | manager, intelligence | Important but non-blocking | Intelligence resolves manager `storage_reference` via `MANAGER_UPLOADS_MOUNT_PATH`, direct paths, or fixtures. | Parsing fails if containers/hosts do not share upload paths. | Standardize shared storage or signed download/read API for intelligence. |
| Mock/live identity drift | UI, manager, intelligence | Important but non-blocking | UI mock data may use code-shaped ids; manager live ids are UUID primary keys. | Live route calls or intelligence artifact lookups can fail if code is passed as id. | Add tests requiring separate `id` and `rfqCode`. |
| UI mock data can mask backend/API failures | UI, manager, intelligence | Important but non-blocking | Mock mode fakes connected health and uses local data. | False confidence during demos/tests. | Always run a live smoke slice before cross-service success claims. |
| Auth alignment incomplete | all | Important but non-blocking | Manager has IAM/auth bypass; intelligence auth not confirmed; UI role hiding is presentation-level. | UI may expose actions backend rejects or appear secure when it is not. | Document permissions per endpoint and add auth integration tests. |
| Public manager token env var | UI, manager | Important but non-blocking | UI reads `NEXT_PUBLIC_MANAGER_API_TOKEN`. | Real secrets in browser would be exposed. | Use only non-secret dev token or move auth to secure server/session flow. |
| Missing frontend export consumer | UI, manager | Nice-to-have | Manager exposes `/rfqs/export`; UI consumer not confirmed. | Export capability may be backend-only. | Add UI feature only if product needs it and test contract. |
| Intelligence artifact freshness ambiguity | UI, intelligence | Important but non-blocking | Snapshot/read model exists, but cross-service freshness rules are not clearly enforced. | UI may show stale artifacts after manager lifecycle/file changes. | Include source timestamps/status in UI and trigger refresh policies. |
| Incomplete environment examples | all | Nice-to-have | Several env vars used in code are missing from `.env.example` files. | Local setup and debugging are error-prone. | Update env examples with safe placeholders and warnings. |
| Missing cross-service contract tests | all | Important but non-blocking | Tests exist per service, but no confirmed integrated contract suite across all three repos. | API/type drift can slip through. | Add generated schema or fixture-based contract tests. |
| Scenario script path not found in current workspace | manager, intelligence | Nice-to-have | Service docs reference parent scenario script, but `microservices/scripts/rfqmgmt_scenario_stack.py` and root `scripts/rfqmgmt_scenario_stack.py` were not present. | Runbook commands may be stale in this workspace. | Locate script in real deployment repo or update docs/runbooks. |

## 17. Cross-Service Drift and Contract Mismatch

| Area | Documented / Expected | Actual | Drift Type | Risk | Suggested Fix |
| --- | --- | --- | --- | --- | --- |
| Manager event integration | Lifecycle events imply async integration potential | Manager event bus is best-effort; intelligence consumer not confirmed | Expected vs implemented | Automation may silently not happen. | Clarify event architecture and implement consumer or remove implication. |
| Workbook event | Intelligence handles `workbook.uploaded` | Manager file upload does not confirmably publish it | Contract mismatch | Workbook parser may not run after upload. | Align upload event emission/consumption. |
| Outcome event | Intelligence handles `outcome.recorded` | Manager status changes publish `rfq.status_changed`, not confirmed outcome event | Contract mismatch | Learning/outcome artifacts may not reflect manager terminal status. | Define outcome producer. |
| UI `.env.example` | Lists mock flag, manager URL, intelligence URL, demo latency | Code also references debug headers and manager API token | Env docs drift | Debug/auth setup confusion. | Add safe commented examples and secret warning. |
| Manager `.env.example` | Lists many core vars | Code also uses `MAX_FILE_SIZE_MB`, `AUTH_BYPASS_PERMISSIONS`, `AUTH_BYPASS_DEBUG_HEADERS_ENABLED` | Env docs drift | Upload/auth behavior can surprise local users. | Add non-secret examples. |
| Intelligence `.env.example` | Lists core app/db/manager URL vars | Code also uses `MANAGER_REQUEST_TIMEOUT_SECONDS`, `MANAGER_UPLOADS_MOUNT_PATH`, `LOCAL_FIXTURES_DIR` | Env docs drift | File resolution and timeouts may be misconfigured. | Add examples and explain path semantics. |
| UI workflow truth test | UI test expects a manager path under frontend tree | Actual manager repo is under `microservices/rfq_manager_ms` in this workspace | Test path drift | Truth-gate test may fail for the wrong reason. | Make test locate repo via env/path config. |
| OpenAPI/docs | Service docs note stale or partial API docs | Code has more complete route surface than some docs | Docs drift | Agents may use wrong endpoint counts/contracts. | Regenerate OpenAPI/docs from app code. |
| Mock data | Expected to mirror real APIs | Mock mode uses local/demo data and faked health | Mock/real mismatch risk | Demos can pass while live integration fails. | Validate mocks against backend fixtures. |

## 18. Integration Testing Recommendations

### 18.1 Backend Contract Tests

- Generate manager OpenAPI from the FastAPI app and assert documented UI-consumed endpoints exist.
- Generate intelligence OpenAPI from the FastAPI app and assert UI-consumed intelligence endpoints exist.
- Add schema tests for manager RFQ list/detail/stage/file/reminder/stats/analytics response shapes.
- Add schema tests for intelligence snapshot, briefing, workbook profile, workbook review, and artifact catalog shapes.
- Add event contract tests for `rfq.created`, `workbook.uploaded`, and `outcome.recorded` envelopes before enabling async integration.

### 18.2 Frontend Contract Tests

- Run UI connector tests against recorded manager and intelligence fixtures from real backend responses.
- Validate mock RFQ, workflow, reminder, stats, analytics, and intelligence objects against the same TypeScript/runtime schemas used for live responses.
- Test that live mode calls `/rfq-manager/v1` and `/intelligence/v1` under the configured base URLs.
- Test that mock mode does not call live health/API endpoints.

### 18.3 End-to-End Business Slice Tests

- Create RFQ through UI, verify manager created RFQ, workflow stages, and `current_stage_id`.
- Open RFQ detail, verify UI stage timeline uses manager stages and current stage.
- Upload an estimation workbook as a manager stage file, trigger intelligence workbook processing, and verify workbook artifact appears in UI.
- Advance a stage through UI, verify manager state changes and UI refetches updated progress.
- Attempt an unauthorized/restricted action when auth is enabled and verify backend rejection is surfaced.
- Delete a stage file through UI and verify manager file metadata/download behavior matches implementation.

### 18.4 Scenario Smoke Tests

Confirmed local commands per service are documented in the service source-of-truth files. A referenced parent scenario script path was not found in this workspace, so the exact cross-service scenario stack command could not be confirmed from repository files currently present.

Minimal manual smoke sequence:

```powershell
# Terminal 1
cd microservices\rfq_manager_ms
uvicorn src.app:app --reload --port 8000

# Terminal 2
cd microservices\rfq_intelligence_ms
uvicorn src.app:app --reload --port 8001

# Terminal 3
cd frontend\rfq_ui_ms
$env:NEXT_PUBLIC_USE_MOCK_DATA="false"
$env:NEXT_PUBLIC_MANAGER_API_URL="http://localhost:8000"
$env:NEXT_PUBLIC_INTELLIGENCE_API_URL="http://localhost:8001"
npm.cmd run dev
```

Health URLs:

- Manager: `http://localhost:8000/health`
- Manager metrics: `http://localhost:8000/metrics`
- Intelligence: `http://localhost:8001/health`
- UI: usually `http://localhost:3000` if the Next.js port is free.

## 19. Recommended Cross-Service Improvement Roadmap

| Priority | Improvement | Services | Why It Matters | Suggested First Step |
| --- | --- | --- | --- | --- |
| 1 | Add contract tests for UI-consumed manager endpoints | UI, manager | Prevents RFQ/stage/reminder/stats drift | Capture manager fixtures and validate UI connector mappings. |
| 2 | Add contract tests for UI-consumed intelligence endpoints | UI, intelligence | Prevents artifact schema/display drift | Capture snapshot/briefing/workbook/review fixtures. |
| 3 | Resolve event contract mismatch | manager, intelligence | Enables reliable automatic intelligence updates | Write shared event payload spec for `rfq.created`, `workbook.uploaded`, `outcome.recorded`. |
| 4 | Decide workbook upload trigger strategy | all | Removes ambiguity after stage file upload | Choose automatic event, explicit UI trigger, or both with clear statuses. |
| 5 | Standardize file access between manager and intelligence | manager, intelligence | Makes parsing deployable beyond local fixtures | Use shared object storage or a backend file retrieval connector. |
| 6 | Fix env example drift | all | Reduces setup failures | Add missing safe env vars with comments and security warnings. |
| 7 | Fix UI workflow truth test path | UI, manager | Avoids false failing validation | Make manager repo path configurable. |
| 8 | Add live-mode UI smoke test | all | Verifies one complete business slice | Start both backends and run Playwright/API smoke path. |
| 9 | Clarify auth model across services | all | Prevents UI role/security confusion | Document endpoint permissions and intelligence auth plan. |
| 10 | Add artifact freshness indicators | UI, intelligence, manager | Reduces stale intelligence risk | Surface source timestamps/status in intelligence panels. |
| 11 | Regenerate OpenAPI/docs | manager, intelligence | Gives agents accurate API contracts | Add docs generation command to CI/manual runbook. |
| 12 | Add cross-service scenario script to this workspace or update references | all | Makes runbooks executable | Restore or document the actual scenario script location. |

## 20. Rules for Future AI Coding Agents

- Read all three service source-of-truth files first.
- Read this cross-service file before multi-service changes.
- Identify the source of truth before editing any behavior.
- Never duplicate backend truth in UI.
- Never change manager API contracts without updating UI types, mocks, tests, and this document.
- Never change intelligence artifact schemas without updating UI consumers, mocks, tests, and this document.
- Never introduce cross-service behavior without documenting the contract and failure behavior.
- Never use mock data as proof of backend integration.
- Never treat UI role hiding as backend security.
- Never use `rfq_code` as a backend path identity unless the backend route explicitly supports it.
- Never make intelligence mutate manager lifecycle state directly.
- Never make manager generate intelligence artifacts.
- Never add parser/workbook/package logic to UI.
- Never hide missing intelligence artifacts with fake summaries.
- Always test one full business slice after cross-service changes.
- Update this file when communication, contracts, env vars, or ownership boundaries change.

## 21. Quick Cross-Service Runbook

### Start `rfq_manager_ms`

```powershell
cd microservices\rfq_manager_ms
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn src.app:app --reload --port 8000
```

Optional manager seed command from service docs:

```powershell
python scripts\seed_rfqmgmt_scenarios.py --batch all
```

Manager docs and health:

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

### Start `rfq_intelligence_ms`

```powershell
cd microservices\rfq_intelligence_ms
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn src.app:app --reload --port 8001
```

Important local config:

```text
MANAGER_MS_BASE_URL=http://localhost:8000
MANAGER_UPLOADS_MOUNT_PATH=<path to manager uploads if parsing manager files>
```

Intelligence docs and health:

- Swagger: `http://localhost:8001/docs`
- Health: `http://localhost:8001/health`

### Start `rfq_ui_ms`

```powershell
cd frontend\rfq_ui_ms
npm install
Copy-Item .env.example .env.local
npm.cmd run dev
```

Mock mode:

```text
NEXT_PUBLIC_USE_MOCK_DATA=true
```

Real API mode:

```text
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_MANAGER_API_URL=http://localhost:8000
NEXT_PUBLIC_INTELLIGENCE_API_URL=http://localhost:8001
```

UI commands:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Get-ChildItem tests -Filter *.test.mjs | Sort-Object Name | ForEach-Object { node $_.FullName }
```

Recommended startup order:

1. Start databases for manager and intelligence.
2. Run manager migrations and seeds.
3. Start `rfq_manager_ms`.
4. Run intelligence migrations.
5. Start `rfq_intelligence_ms` with `MANAGER_MS_BASE_URL` pointing to manager.
6. Start `rfq_ui_ms` in real API mode.
7. Check `/health` for both backends.
8. Load UI dashboard, RFQ list, RFQ detail, and one intelligence panel.

Could not confirm an executable shared scenario stack command from the current workspace because the referenced parent `rfqmgmt_scenario_stack.py` path was not present under root or `microservices/scripts`.

## 22. Final Architectural Verdict

The strongest part of the platform is the intended separation of truth: manager owns operational lifecycle state, intelligence owns deterministic derived artifacts, and UI owns presentation plus explicit API integration. The implementation mostly respects that boundary: UI calls backend APIs, intelligence reads manager context through a connector, and manager does not embed workbook/package parsing.

The fragile part is the integration glue. Event names and trigger expectations do not yet form a fully closed loop, file parsing depends on shared path/mount assumptions, mock data can obscure live contract drift, and auth/role behavior is not uniformly enforced across all services. The most important thing to protect is the truth hierarchy: never let UI invent lifecycle or intelligence truth, never let intelligence mutate manager lifecycle state, and never let manager absorb parser/artifact responsibilities.

The best next cross-service improvement is to add contract tests around the exact UI-consumed manager and intelligence endpoints, then resolve the workbook/intake event trigger path so file upload, parsing, artifact generation, and UI display become one tested business slice.
