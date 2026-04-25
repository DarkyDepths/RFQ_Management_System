# rfq_ui_ms — Source of Truth for AI Agents

## 1. Purpose of This Document

This document is the canonical technical context for future AI coding agents working on `rfq_ui_ms`. It is based on the implementation in this repository as inspected on 2026-04-25. If this document disagrees with code, the code wins and this file must be updated.

## 2. Frontend Summary

`rfq_ui_ms` is a Next.js App Router frontend for the RFQ platform. It renders dashboards, RFQ portfolio views, RFQ creation, RFQ detail, operational stage workspaces, reminders, role-specific navigation, and intelligence artifact panels by consuming `rfq_manager_ms` and `rfq_intelligence_ms` through typed connector and translator layers. It supports a demo/mock mode controlled by environment variables and a live API mode that calls backend HTTP APIs.

## 3. Product Role

This frontend is the user experience layer for the RFQ lifecycle platform. It helps executives observe portfolio health, managers operate RFQ lifecycle work, and estimators work on assigned RFQs. It displays operational truth from `rfq_manager_ms` and derived intelligence from `rfq_intelligence_ms`; it must not become the owner of lifecycle state, permissions, parser outputs, or persistence.

## 4. Ownership Boundary

### 4.1 What rfq_ui_ms Owns

- Next.js route composition and screen rendering.
- Role-based presentation and navigation for `executive`, `manager`, and `estimator`.
- Dashboard, overview, RFQ list, RFQ create, RFQ detail, and reminder center screens.
- UI state for filters, tabs, local forms, dialogs, toasts, loading, empty, and error states.
- Typed frontend models for manager and intelligence API contracts.
- HTTP connector calls to `rfq_manager_ms` and `rfq_intelligence_ms`.
- Translator functions that map backend/demo payloads into UI models.
- Mock/demo datasets and demo-only mutations behind explicit mock mode.
- Theme switching and app shell state.
- Presentation of intelligence snapshots, briefings, workbook profiles, workbook reviews, artifact catalogs, and reprocess/trigger actions where connectors exist.

### 4.2 What rfq_ui_ms Does Not Own

- RFQ lifecycle truth, status truth, current stage truth, blocker truth, reminder truth, or workflow progression truth.
- Backend permission enforcement or authentication security.
- `rfq_manager_ms` database records, migrations, lifecycle rules, or operational validation.
- `rfq_intelligence_ms` artifact generation, workbook parsing, package parsing, parser reports, or readiness conclusions.
- Chatbot reasoning, LLM behavior, historical learning, estimator judgment, or document intelligence.
- Direct database access.

### 4.3 Partial Seams / Stubs

- Auth/IAM is not fully implemented in the UI. Role switching is localStorage-based presentation behavior.
- Manager debug actor headers exist only when `NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED=true`; they are not a secure auth mechanism.
- `NEXT_PUBLIC_MANAGER_API_TOKEN` can add a browser-visible bearer token; because it is `NEXT_PUBLIC`, it must not contain production secrets.
- Reminder APIs are live-only; mock mode intentionally returns unavailable messages for reminder center and RFQ reminder hooks.
- Stage workspace mutations are live-only; demo mode blocks stage mutation functions.
- Leadership Notes are demo-only; live mode throws an unavailable error.
- Intelligence portfolio summary is mock-only; live mode throws an unavailable error.
- Health checks call `/health` on backend base URLs, not the prefixed API paths.
- No Dockerfile or docker-compose file was found for this frontend.

## 5. Current Implementation Snapshot

| Item | Current implementation |
|---|---|
| framework | Next.js `^15.5.15` App Router |
| runtime | Node.js / browser React runtime |
| package manager | npm (`package-lock.json` present) |
| language | TypeScript, React 18 |
| styling approach | Tailwind CSS, CSS variables in `src/app/globals.css`, shadcn-style local UI primitives, `lucide-react`, `framer-motion` |
| routing approach | `src/app` App Router with `(dashboard)` route group |
| API integration mode | Connector functions under `src/connectors/manager` and `src/connectors/intelligence` |
| mock mode support | `NEXT_PUBLIC_USE_MOCK_DATA=true` enables demo data |
| backend URLs | Manager default `http://localhost:8000`, intelligence default `http://localhost:8001` |
| role support | `executive`, `manager`, `estimator` in `src/models/ui/role.ts` and role config |
| main pages | `/`, `/dashboard`, `/overview`, `/rfqs`, `/rfqs/new`, `/rfqs/[rfqId]`, `/reminders` |
| main components | `DashboardScreen`, `RFQOverviewScreen`, `RFQListScreen`, `RFQCreateScreen`, `RFQDetailScreen`, `RfqOperationalWorkspace`, `IntelligencePanel`, `ReminderCenterPanel` |
| test status | `npm.cmd run typecheck` passed; `npm.cmd run lint` passed; `npm.cmd run build` passed with escalated sandbox permissions; 11 of 12 local Node truth-gate tests passed when excluding one path-layout failure |
| Docker status | Could not confirm from repository. No Dockerfile or compose file found in `frontend/rfq_ui_ms`. |
| CI status if visible | Could not confirm from repository. |
| implementation maturity | Functional frontend shell with strong mock/live separation for many flows; several seams remain demo-only or live-only. |

## 6. Repository Structure

```text
frontend/rfq_ui_ms/
  .env.example
  README.md
  package.json
  package-lock.json
  next.config.mjs
  tailwind.config.ts
  tsconfig.json
  postcss.config.js
  scripts/
  public/
  tests/
  src/
    app/
    components/
    config/
    connectors/
    context/
    demo/
    hooks/
    lib/
    models/
    translators/
    utils/
```

| Path | Role |
|---|---|
| `src/app/` | App Router pages, global layout, global CSS, app icon. |
| `src/components/` | Screen, layout, domain, intelligence, reminder, common, branding, and local UI components. |
| `src/config/` | API settings, app labels, navigation, role capabilities, role permissions, theme, industry options. |
| `src/connectors/manager/` | HTTP/mock access to `rfq_manager_ms` resource families. |
| `src/connectors/intelligence/` | HTTP/mock access to `rfq_intelligence_ms` artifacts and triggers. |
| `src/context/` | Role, theme, toast, connection, and app-shell providers. |
| `src/demo/` | Mock manager and intelligence payloads plus demo-only mutators. |
| `src/hooks/` | Reusable client-side loading, filtering, refresh, and mutation state. |
| `src/lib/` | Shared client helpers for HTTP, actor headers, access checks, RFQ display, executive insights. |
| `src/models/` | TypeScript frontend contracts for manager, intelligence, and UI models. |
| `src/translators/` | Mapping from API/demo payloads to UI models. |
| `src/utils/` | Formatting, workflow selection/deadline helpers, stage captured-data helpers, reminder/subtask validation, status helpers. |
| `tests/` | Node `.mjs` truth-gate tests; not wired into `package.json` as `npm test`. |
| `scripts/dev.mjs` | Deletes `.next` then starts Next dev with Turbopack. |
| `scripts/repro-dev-open-error.mjs` | Local repro/probe script with hardcoded `d:/PFE/rfq_ui_ms` path. |
| `public/brand/albassam-logo.png` | Brand image used by UI. |
| `docs/` | Did not exist before this source-of-truth file was created. |

Folders not present: `src/services`, `src/api`, `src/store`, `src/providers`, `src/constants`, `src/styles`, top-level `pages`, top-level `app`.

## 7. Frontend Architecture Mapping

| Layer | Responsibility | Actual examples | Future agents must not do |
|---|---|---|---|
| `app/` | Route files and layout composition. | `src/app/layout.tsx` wraps providers; pages render screen components. | Do not place complex API logic, lifecycle decisions, or parser logic in page files. |
| `components/` | Reusable UI and screen rendering. | `RFQDetailScreen`, `RfqOperationalWorkspace`, `IntelligencePanel`, `ReminderCenterPanel`. | Do not duplicate backend lifecycle rules or generate intelligence locally. |
| `lib/` | Shared client helpers and access helpers. | `http-client.ts`, `manager-actor.ts`, `rfq-access.ts`, `executive-insights.ts`. | Do not let helpers become hidden backend simulators. |
| `connectors/` | Backend HTTP and explicit mock/live branching. | `manager/rfqs.ts`, `manager/stages.ts`, `intelligence/workbook.ts`. | Do not mix mock and real data silently or hardcode production URLs. |
| `hooks/` | Client data loading and interaction state. | `use-rfq-list`, `use-rfq-detail`, `use-rfq-intelligence`, `use-reminder-center`. | Do not hide backend mutations or fake success inside hooks. |
| `context/` | Cross-app UI state. | `RoleProvider`, `ThemeProvider`, `ToastProvider`, `ConnectionProvider`, `AppShellProvider`. | Do not treat local context role as secure backend permission enforcement. |
| `models/` | Frontend DTO and UI contracts. | `models/manager/api-rfq.ts`, `models/intelligence/api.ts`, `models/ui/role.ts`. | Do not change types without checking backend contracts and translators. |
| `translators/` | Payload-to-view-model mapping. | Manager RFQ/stage/workflow/reminder translators; intelligence snapshot/briefing/workbook translators. | Do not add backend calls or mutation side effects here. |
| `utils/` | Pure helpers and validation helpers. | `workflow-selection.ts`, `subtask.ts`, `reminder.ts`, `go-no-go.ts`. | Do not turn utilities into an orchestration layer. |
| `config/` | Runtime and UI configuration. | `api.ts`, `navigation.ts`, `role-capabilities.ts`, `role-permissions.ts`. | Do not hardcode environment-specific values outside config. |
| `styles/` | Styling lives in `src/app/globals.css` and Tailwind config. | No separate `src/styles` folder. | Do not split styling into untracked conventions without documenting it. |
| `public/` | Static assets. | `public/brand/albassam-logo.png`. | Do not put data contracts or mock APIs in static assets. |
| `tests/` | Node truth-gate and helper tests. | `p0-truth-gates.test.mjs`, `stage-workspace-phase4.test.mjs`. | Do not claim behavior is tested by browser/e2e tests unless added. |

Golden rule:

```text
User interaction
  -> page/component
  -> hook/service/API client
  -> backend HTTP API
  -> typed response
  -> UI rendering
```

Forbidden patterns:

- UI directly inventing lifecycle state.
- UI treating mock data as real data.
- UI bypassing backend permissions.
- UI duplicating stage transition rules instead of invoking manager APIs.
- UI generating intelligence artifacts locally.
- UI hiding backend errors with fake success.
- UI hardcoding RFQ IDs/codes outside explicit demo/mock paths.
- UI mixing mock and real data in the same runtime path without clear separation.

## 8. App Startup and Configuration

- `src/app/layout.tsx` defines root HTML, imports global CSS and Google fonts, and wraps the app in `ThemeProvider`, `ToastProvider`, `RoleProvider`, `ConnectionProvider`, and `AppShellProvider`.
- `src/app/(dashboard)/layout.tsx` wraps dashboard routes in `AppShell`.
- `src/app/page.tsx` redirects by role: executives go to `/dashboard`; managers and estimators go to `/overview`.
- `npm run dev` runs `node scripts/dev.mjs`, which removes `.next`, sets `NODE_PATH`, then runs Next dev with `--turbo`.
- `npm run build` runs `next build`.
- `npm run start` runs `next start`.
- `npm run lint` runs deprecated `next lint`; it passed during inspection but Next says it will be removed in Next.js 16.
- Environment variables are read through `src/config/api.ts` and `src/config/navigation.ts`.
- Mock mode is enabled only when `NEXT_PUBLIC_USE_MOCK_DATA === "true"`.
- Live mode is used for every other value, including unset.
- Connection health checks run only in live mode and poll `/health` on both base URLs every 30 seconds.
- There is no middleware file in this repository.

## 9. Environment Variables

| Name | Purpose | Required/optional | Example value | Mock-mode behavior | Real API behavior | Security notes |
|---|---|---|---|---|---|---|
| `NEXT_PUBLIC_USE_MOCK_DATA` | Enables demo data when exactly `"true"`. | Optional; defaults to live mode if unset. | `true` | Uses `src/demo` data and mock connector branches. | Must be `false` or unset to call live APIs. | Public browser env var; not secret. |
| `NEXT_PUBLIC_MANAGER_API_URL` | Manager backend base URL. | Optional; default `http://localhost:8000`. | `http://localhost:8000` | Mostly unused except health mode is demo-connected. | Base for `/rfq-manager/v1` API paths and `/health`. | Public URL. |
| `NEXT_PUBLIC_INTELLIGENCE_API_URL` | Intelligence backend base URL. | Optional; default `http://localhost:8001`. | `http://localhost:8001` | Mostly unused except health mode is demo-connected. | Base for `/intelligence/v1` API paths and `/health`. | Public URL. |
| `NEXT_PUBLIC_DEMO_LATENCY_MS` | Artificial demo latency in milliseconds. | Optional; default `650`. | `650` | Used by `sleep()` in mock connectors. | No direct effect on live HTTP. | Public value. |
| `NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED` | Enables manager actor debug headers. | Optional; default disabled. | `true` | Not needed for mock data. | Adds `X-Debug-User-*` and `X-Debug-Permissions` headers. | Debug-only; not security. |
| `NEXT_PUBLIC_MANAGER_API_TOKEN` | Optional bearer token for manager requests. | Optional. | Do not store real secrets here. | No practical mock effect. | Adds `Authorization: Bearer <token>` through `http-client.ts`. | Because it is `NEXT_PUBLIC`, it is exposed to the browser and must not hold production secrets. |

`.env.example` documents the first four variables only. The debug header flag and token are referenced in code but not listed there.

## 10. Routing and Pages

| Path | File path | Purpose | Main components used | Data source | Role visibility if implemented | Mock/real behavior | Known risks |
|---|---|---|---|---|---|---|---|
| `/` | `src/app/page.tsx` | Role-based redirect. | None beyond loading spinner. | `RoleProvider`. | All roles. | Same in mock/live. | Redirect depends on local role only. |
| `/dashboard` | `src/app/(dashboard)/dashboard/page.tsx` | Portfolio dashboard. | `DashboardScreen`, executive visuals, KPI cards. | `useDashboardData`. | Navigation exposes to executive and manager. Component rejects roles without portfolio access. | Executive data is computed from RFQ list and leadership notes; manager uses stats/analytics connectors. | Some executive metrics are client-derived from loaded list. |
| `/overview` | `src/app/(dashboard)/overview/page.tsx` | Manager/estimator operational overview. | `RFQOverviewScreen`, `ReminderCenterSummaryCard`. | `useOverviewData`, reminder summary. | Manager and estimator nav; executive gets empty-state unavailable message. | Mock uses demo RFQs; live calls manager RFQ/stats endpoints. | Estimator metrics can be client-computed from scoped list. |
| `/rfqs` | `src/app/(dashboard)/rfqs/page.tsx` | RFQ monitor/queue. | `RFQListScreen`, `RFQCard`, `RFQTable`. | `useRfqList`. | All roles in navigation, with labels differing by role. | Mock status filters include demo statuses; live filters only supported manager statuses. | Status/filter shapes differ between demo and live by design. |
| `/rfqs/new` | `src/app/(dashboard)/rfqs/new/page.tsx` | Create RFQ form. | `RFQCreateScreen`. | `listWorkflows`, `createRfq`. | Manager and estimator; executive lacks create permission. | Mock create mutates demo memory; live POSTs to manager. | Default form values are demo-friendly and should not be treated as backend defaults. |
| `/rfqs/[rfqId]` | `src/app/(dashboard)/rfqs/[rfqId]/page.tsx` | RFQ detail. | `RFQDetailScreen`, `RfqOperationalWorkspace`, `IntelligencePanel`, `LeadershipNotesPanel`, `ExecutiveStrategicDetail`, `ArtifactCard`. | Manager detail/stages/current stage; intelligence resources. | Tabs differ by role; access helpers scope estimators. | Mock detail/intelligence data available; stage workspace mutations live-only; leadership notes demo-only. | Detail route accepts any `rfqId`; backend authorization remains authoritative. |
| `/reminders` | `src/app/(dashboard)/reminders/page.tsx` | Service-wide reminder center. | `ReminderCenterScreen`, `ReminderCenterPanel`. | `useReminderCenter`. | Manager-only in screen and navigation. | Mock mode displays live-only unavailable state; live calls manager reminder APIs. | UI-only role restriction. |

## 11. API Integration

### 11.1 rfq_manager_ms Integration

Manager connector base:

- Base URL: `apiConfig.managerBaseUrl`.
- API prefix: `/rfq-manager/v1`.
- HTTP wrapper: `requestManagerJson` in `src/connectors/manager/base.ts`.
- Optional auth: browser-visible bearer token from `NEXT_PUBLIC_MANAGER_API_TOKEN`.
- Optional debug actor headers: `buildManagerActorHeaders`.

| Frontend function | File path | Backend service | HTTP method/path | Expected request shape | Expected response shape | Loading/error behavior | Mock equivalent | Consumers |
|---|---|---|---|---|---|---|---|---|
| `listRfqs` | `src/connectors/manager/rfqs.ts` | manager | `GET /rfqs` with `page`, `size`, `search`, `sort`, `status` | Query params | `ManagerApiRfqListResponse` | Errors surface through hooks. Unsupported live status filter throws. | Filters `managerRfqListResponse.items`. | `use-rfq-list`, dashboards, breadcrumbs indirectly |
| `getRfqDetail` | same | manager | `GET /rfqs/{rfqId}`, then `GET /rfqs/{rfqId}/stages`, optional `GET /rfqs/{rfqId}/stages/{currentStageId}` | Path params | `ManagerApiRfqDetail` plus stage data | `useRfqDetail` sets error and null. | Looks up `managerRfqDetailResponses`. | RFQ detail, breadcrumbs |
| `createRfq` | same | manager | `POST /rfqs` | name, client, deadline, owner, workflow_id, skip_stages, industry, country, priority, description | RFQ detail translated to mutation result | Create screen displays validation/API error. | `createDemoRfq` mutates demo arrays. | RFQ create |
| `updateRfqRecord` | same | manager | `PATCH /rfqs/{rfqId}` | core metadata and `outcome_reason` | RFQ detail translated to mutation result | Operational workspace `runAction` displays errors. | `updateDemoRfq` mutates demo data. | Operational workspace |
| `cancelRfqRecord` | same | manager | `POST /rfqs/{rfqId}/cancel` | `outcome_reason` | RFQ detail translated to mutation result | Dialog validates reason, refreshes on success. | `cancelDemoRfq`. | Operational workspace |
| `getDashboardMetrics` | same | manager | `GET /rfqs/stats` | none | `ManagerApiRfqStats` | Dashboard hook sets error. | Computes safe metrics; avg cycle unavailable. | Dashboard/overview |
| `getDashboardAnalytics` | same | manager | `GET /rfqs/analytics` | none | `ManagerApiRfqAnalytics` | Dashboard hook sets error. | Computes win rate/by-client; margin/accuracy unavailable. | Dashboard |
| `listWorkflows` | `src/connectors/manager/workflows.ts` | manager | `GET /workflows`, then `GET /workflows/{id}` for each | none | list plus detail | Create screen shows workflow load error. | `managerWorkflowResponses`. | Create screen |
| `getWorkflow` | same | manager | `GET /workflows/{workflowId}` | path param | `ManagerApiWorkflowDetail` | Operational workspace handles null/error. | Demo workflow lookup. | Workspace |
| `getWorkflowStages` | `src/connectors/manager/stages.ts` | manager | `GET /workflows/{workflowId}` | path param | detail `stages` | Errors surface to caller. | Demo workflow stages. | Stage display/workspace |
| `getRfqStages` | same | manager | `GET /rfqs/{rfqId}/stages` | path param | `ManagerApiStageListResponse` | Errors surface through hook/caller. | Demo `stageHistory`. | RFQ detail |
| `getStageDetail` | same | manager | `GET /rfqs/{rfqId}/stages/{stageId}` | path params | `ManagerApiStageDetail` | Returns null if no stage id. | Returns null in mock. | Workspace/history |
| `updateStage` | same | manager | `PATCH /rfqs/{rfqId}/stages/{stageId}` | captured_data, blocker_status, blocker_reason_code | stage detail translated | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `advanceStage` | same | manager | `POST /rfqs/{rfqId}/stages/{stageId}/advance` | confirm_no_go_cancel, terminal_outcome, lost_reason_code, outcome_reason | stage detail translated | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `addStageNote` | same | manager | `POST /rfqs/{rfqId}/stages/{stageId}/notes` | text | note | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `uploadStageFile` | same | manager | `POST /rfqs/{rfqId}/stages/{stageId}/files` | `FormData` file and type | stage file | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `deleteStageFile` | same | manager | `DELETE /files/{fileId}` | file id | void | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `createSubtask` | same | manager | `POST /rfqs/{rfqId}/stages/{stageId}/subtasks` | name, assigned_to, due_date | void then UI refresh | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `updateSubtask` | same | manager | `PATCH /rfqs/{rfqId}/stages/{stageId}/subtasks/{subtaskId}` | name, assigned_to, due_date, progress, status | void then UI refresh | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `deleteSubtask` | same | manager | `DELETE /rfqs/{rfqId}/stages/{stageId}/subtasks/{subtaskId}` | ids | void then UI refresh | Demo mode throws disabled message. | None; live-only. | Operational workspace |
| `listStageNotes` | same | manager | live via stage detail | ids | note list | Errors surface to caller. | Demo maps `stageNotes`. | Workspace/history |
| `listStageFiles` | same | manager | live via stage detail | ids | file list | Errors surface to caller. | Demo maps `recentFiles`. | Workspace/history |
| `listSubtasks` | same | manager | live via stage detail | ids | subtask list | Errors surface to caller. | Demo maps `subtasks`. | Workspace/history |
| `listReminders` | `src/connectors/manager/reminders.ts` | manager | `GET /reminders` | rfq_id, status, user query params | `ManagerApiReminderListResponse` | Hooks show unavailable/error. | Empty list in mock. | Reminder center/RFQ reminders |
| `getReminderStats` | same | manager | `GET /reminders/stats` | none | `ManagerApiReminderStats` | Hooks show unavailable/error. | zero stats in mock connector, but hooks explicitly mark live-only. | Reminder summary/center |
| `getReminderRules` | same | manager | `GET /reminders/rules` | none | `ManagerApiReminderRuleListResponse` | Center hook sets error. | Empty rules in mock connector, but hook marks live-only. | Reminder center |
| `createReminder` | same | manager | `POST /reminders` | rfq_id, rfq_stage_id, type, message, due_date, assigned_to | void then UI refresh | Mock throws live-only message. | None; live-only. | Workspace |
| `resolveReminder` | same | manager | `POST /reminders/{id}/resolve` | reminder id | void then UI refresh | Mock throws live-only message. | None; live-only. | Workspace/center |
| `processReminders` | same | manager | `POST /reminders/process` | none | `{message}` | Center shows toast. | None; live-only. | Reminder center |
| `sendReminderTestEmail` | same | manager | `POST /reminders/test` | none | `{message}` | Center shows toast. | None; live-only. | Reminder center |
| `updateReminderRule` | same | manager | `PATCH /reminders/rules/{ruleId}` | `is_active` | void then refresh | Center shows toast/error. | None; live-only. | Reminder center |
| Leadership note functions | `src/connectors/manager/leadership-notes.ts` | manager seam | No live endpoints used | demo inputs | demo threads | Live mode throws unavailable error. | Demo-only mutable threads. | Leadership notes panel, executive filters |

### 11.2 rfq_intelligence_ms Integration

Intelligence connector base:

- Base URL: `apiConfig.intelligenceBaseUrl`.
- API prefix: `/intelligence/v1`.
- HTTP wrapper: `requestIntelligenceJson` in `src/connectors/intelligence/base.ts`.
- No auth or debug headers in code.

| Frontend function | File path | Backend service | HTTP method/path | Expected request shape | Expected response shape | Loading/error behavior | Mock equivalent | Consumers |
|---|---|---|---|---|---|---|---|---|
| `getIntelligenceSnapshot` | `src/connectors/intelligence/snapshot.ts` | intelligence | `GET /rfqs/{rfqId}/snapshot` | rfq id | `IntelligenceArtifactEnvelope<IntelligenceSnapshotContent>` | 404 returns null; other errors surface. | `snapshotResponses`. | `useRfqIntelligence`, `IntelligencePanel` |
| `getIntelligencePortfolioSummary` | same | intelligence seam | No live endpoint used | none | `IntelligencePortfolioModel` | Live throws not connected error. | `intelligencePortfolioResponse`. | Could not confirm active consumer from code inspection. |
| `getBriefingArtifact` | `src/connectors/intelligence/briefing.ts` | intelligence | `GET /rfqs/{rfqId}/briefing` | rfq id | `IntelligenceArtifactEnvelope<IntelligenceBriefingContent>` | 404 returns null. | `briefingResponses`. | `useRfqIntelligence`, `IntelligencePanel` |
| `getWorkbookProfile` | `src/connectors/intelligence/workbook.ts` | intelligence | `GET /rfqs/{rfqId}/workbook-profile` | rfq id | `IntelligenceArtifactEnvelope<IntelligenceWorkbookProfileContent>` | 404 returns null. | `workbookProfileResponses`. | `useRfqIntelligence`, `IntelligencePanel` |
| `getWorkbookReview` | same | intelligence | `GET /rfqs/{rfqId}/workbook-review` | rfq id | `IntelligenceArtifactEnvelope<IntelligenceWorkbookReviewContent>` | 404 returns null. | `workbookReviewResponses`. | `useRfqIntelligence`, `IntelligencePanel` |
| `getArtifactCatalog` | `src/connectors/intelligence/artifacts.ts` | intelligence | `GET /rfqs/{rfqId}/artifacts` | rfq id | `IntelligenceArtifactIndexResponse` | Errors captured by `useRfqIntelligence`. | `artifactResponses`. | RFQ detail artifacts tab |
| `requestArtifactReprocess` | same | intelligence | `POST /rfqs/{rfqId}/reprocess/{kind}` | kind `intake` or `workbook` | `IntelligenceReprocessResponse` | Actions panel shows message/error. | Accepted demo result. | `IntelligenceActionsPanel` |
| `triggerIntelligenceIntake` | `src/connectors/intelligence/triggers.ts` | intelligence | `POST /rfqs/{rfqId}/trigger/intake` | rfq id | trigger result | Actions panel shows message/error. | Demo processed result. | `useRfqIntelligence` actions |
| `triggerIntelligenceWorkbook` | same | intelligence | `POST /rfqs/{rfqId}/trigger/workbook` | workbook_ref, workbook_filename, uploaded_at | trigger result | Actions panel shows message/error. | Demo processed result. | `useRfqIntelligence` actions |
| `triggerIntelligenceOutcome` | same | intelligence | `POST /rfqs/{rfqId}/trigger/outcome` | outcome, outcome_reason, recorded_at | trigger result | Actions panel shows message/error. | Demo processed result. | `useRfqIntelligence` actions |

## 12. Mock Data and Real API Mode

- Mock data lives under `src/demo/manager` and `src/demo/intelligence`.
- Mock mode is enabled only by `NEXT_PUBLIC_USE_MOCK_DATA=true`.
- Real API mode is enabled by setting that variable to any non-`true` value or leaving it unset.
- Connector modules are the only intended place for mock/live branching.
- Some demo data mutates in browser memory (`createDemoRfq`, `updateDemoRfq`, `cancelDemoRfq`, leadership notes).
- Reminder and stage mutation flows are intentionally not mocked.
- Mock and live shapes do not fully match because demo supports richer demo statuses and demo-only leadership notes.

| Mock Source | Real API Equivalent | Shape Match | Risk | Suggested Fix |
|---|---|---|---|---|
| `src/demo/manager/rfqs.ts` | `/rfq-manager/v1/rfqs`, stats, analytics, detail/stages | Partial | Demo-only statuses and hardcoded sample RFQs can drift from manager schema. | Keep translator tests and add contract tests against manager OpenAPI when available. |
| `src/demo/manager/workflows.ts` and `stages.ts` | `/workflows`, `/workflows/{id}` | Partially guarded by tests | `workflow-catalog-truth.test.mjs` expects a sibling manager repo path that is absent in this workspace layout. | Make the test locate manager repo robustly or document workspace layout requirement. |
| `src/demo/manager/leadership-notes.ts` | None connected in live mode | No live equivalent | UI can imply a feature exists live when connector throws. | Keep labels explicit that leadership notes are demo-only until backend exists. |
| `src/demo/intelligence/snapshot.ts` | `/intelligence/v1/rfqs/{id}/snapshot` | Partial | Demo has legacy `SnapshotResponse`; live uses artifact envelopes. | Continue translating both paths and add fixture tests for live envelopes. |
| `src/demo/intelligence/briefing.ts` | `/briefing` artifact envelope | Partial | Legacy demo response differs from live artifact content model. | Maintain separate translators and test both shapes. |
| `src/demo/intelligence/workbook.ts` | `/workbook-profile`, `/workbook-review` envelopes | Partial | Demo workbook profile/review shape is simpler than live parser artifact content. | Add live fixture tests before changing workbook panels. |
| `src/demo/intelligence/artifacts.ts` | `/artifacts` index | Partial | Demo artifact kind names differ from live artifact types and are mapped by translator. | Keep `mapArtifactTypeToKind` aligned with intelligence backend. |

## 13. Type System and Data Contracts

| Type/file | Purpose | Backend alignment risk |
|---|---|---|
| `src/models/ui/role.ts` | Defines `AppRole = "executive" | "manager" | "estimator"`. | Local-only role model; not backend auth. |
| `src/models/ui/dashboard.ts` | KPI, analytics, intelligence portfolio, breadcrumb models. | Dashboard can combine backend and client-derived metrics. |
| `src/models/manager/api-rfq.ts` | Live manager RFQ DTOs for list/detail/stats/analytics/create/update/cancel. | Must stay aligned with `rfq_manager_ms`. |
| `src/models/manager/rfq.ts` | UI manager RFQ models, demo responses, reminders, files, subtasks, create/update inputs. | Mixes demo-only statuses with live statuses; translators separate display. |
| `src/models/manager/api-stage.ts` | Live stage detail, notes, files, subtasks, update/advance inputs. | Stage workspace depends on `captured_data` and `mandatory_fields` semantics. |
| `src/models/manager/stage.ts` | Stage progress, workspace, lifecycle event, update/advance UI models. | UI must not own lifecycle decisions. |
| `src/models/manager/api-workflow.ts` and `workflow.ts` | Live and UI workflow contract. | Create RFQ depends on `selection_mode`, required stages, planned durations. |
| `src/models/manager/api-reminder.ts` | Live reminder DTOs/rules/stats. | Reminder UI is live-only; mock behavior intentionally limited. |
| `src/models/manager/leadership-note.ts` | Demo leadership note threads. | No live equivalent currently. |
| `src/models/intelligence/api.ts` | Live intelligence artifact envelope and content contracts. | High risk if intelligence backend artifact schemas change. |
| `src/models/intelligence/snapshot.ts` | Demo snapshot response and UI snapshot model. | Live snapshot is translated from envelope content, not this legacy response. |
| `src/models/intelligence/briefing.ts` | Demo briefing and UI briefing model. | Live briefing uses `IntelligenceBriefingContent`. |
| `src/models/intelligence/workbook.ts` | Demo workbook profile/review and UI workbook models. | Live workbook content includes parser/template/pairing details; tests should cover changes. |
| `src/models/intelligence/artifacts.ts` | Artifact catalog and reprocess models. | Live artifact type mapping must remain complete. |
| `src/models/intelligence/triggers.ts` | Intelligence lifecycle trigger result models. | Trigger payload expectations must match `rfq_intelligence_ms`. |

## 14. Role-Based UI Behavior

- Current role is stored by `RoleProvider` in `localStorage` key `rfq-ui-ms-role`.
- `RoleSwitcher` changes role and refreshes the router.
- Default role is `manager` from `appConfig.defaultRole`.
- Role capabilities are declared in `src/config/role-capabilities.ts`.
- Boolean presentation permissions are derived in `src/config/role-permissions.ts`.
- Scoped estimator access is based on RFQ owner matching the current actor name from `manager-actor.ts`.
- Backend permission checks are not implemented in the UI; backend remains authoritative.

| Role | Visible Areas | Allowed UI Actions | Restricted UI Actions | Backend Dependency | Risk |
|---|---|---|---|---|---|
| Executive | Dashboard, RFQ Monitor, RFQ detail intelligence tab, featured demo detail in mock mode. | Portfolio viewing, intelligence summary/supportive read, leadership note create/read. | No create RFQ, no operational workspace, no stage advance, no reminders management, no artifact diagnostics tab. | Backend must enforce real auth/permissions. | UI-derived executive metrics and demo leadership notes can look official if not labeled carefully. |
| Estimation Manager | Dashboard, Overview, RFQ Queue, Create RFQ, Reminder Center, RFQ detail operational/intelligence/artifacts tabs. | Create/update RFQs, stage workspace update/advance, notes/files/subtasks/reminders, intelligence triggers/reprocess, leadership note reply/close. | Subject to terminal RFQ and form validations. | Manager backend enforces lifecycle and permission truth. | UI has broad controls; backend rejection must remain visible. |
| Estimator | Overview, RFQ Queue, Create RFQ, RFQ detail operational/intelligence/artifacts tabs for scoped RFQs. | Create RFQ, read/update assigned RFQs, manage subtasks, upload/download/delete own files for assigned RFQs. | No portfolio dashboard, no stage advance, no core lifecycle controls, no reminder management, no leadership notes. | Backend must enforce assigned-scope access. | Owner-name matching is presentation-only and not secure. |

## 15. Core User Workflows

### 15.1 Dashboard / Portfolio View

`DashboardScreen` uses `useDashboardData(role, permissions)`.

- Executives load RFQs with `listRfqs({ size: 100 })`, load demo/live leadership notes through `listLeadershipNotes`, and compute portfolio KPIs, lifecycle distribution, delay drivers, loss reasons, and leadership attention items on the client.
- Managers load `getDashboardMetrics()` and `getDashboardAnalytics()`.
- Users without portfolio access see an `EmptyState`.
- Loading uses `SkeletonCard`.
- Errors use `EmptyState`.
- Mock mode uses demo RFQs and computed demo metrics. Live mode calls manager APIs for manager dashboard metrics/analytics.

### 15.2 RFQ List / Search

`RFQListScreen` uses `useRfqList`.

- Search is stored in component state and deferred before connector calls.
- Status filters are mock/live-aware. Mock mode allows demo statuses; live mode only supports `in_preparation`, `awarded`, `lost`, `cancelled`, or `all`.
- Query params can carry executive drilldown filters such as signal and leadership filters.
- View mode toggles between card and table rendering.
- Sorting is implemented in `RFQTable`.
- Pagination is not implemented in the UI beyond requesting size `100` from the connector.

### 15.3 Create RFQ

`RFQCreateScreen` is implemented.

- Loads workflows via `listWorkflows`.
- Form fields include title/name, client, owner, value input for display context, due date, priority, industry/custom industry, country, description, workflow, and customizable stage selection.
- Required validation checks title, client, owner, industry, country, due date, workflow, and at least one selected workflow stage.
- Due date cannot be in the past.
- If workflow durations are known, due date must be at or after the minimum feasible workflow date.
- Required workflow stages are locked in customizable workflow selection.
- Live create posts to manager with `skipStageIds` converted to `skip_stages`.
- Mock create mutates demo memory and returns a generated `RFQ-2026-####` style id.
- Success redirects to `/rfqs/{result.id}?created=1`; `RFQDetailScreen` then shows a success toast.

### 15.4 RFQ Detail / Overview

`RFQDetailScreen` uses `useRfqDetail` and `useRfqIntelligence`.

- Manager detail includes RFQ metadata, status, progress, current stage, stage history, package/workbook availability flags, source update timestamps, notes, files, subtasks, and uploads where available.
- Visible tabs come from role permissions: executive sees intelligence; manager/estimator see operational, intelligence, and artifacts.
- `ExecutiveStrategicDetail` renders executive-specific strategic cards.
- `LeadershipNotesPanel` appears where role permissions allow.
- The artifacts tab renders `ArtifactCard` for artifact catalog results.
- Missing RFQ or inaccessible lifecycle shows `EmptyState`.

### 15.5 Stage Timeline and Progress

- `RFQStageTimeline` renders `stageHistory` from manager/detail/demo data.
- `LifecycleProgressStageBox` renders RFQ lifecycle progress and current stage state in RFQ cards/tables.
- Live RFQ cards use backend `progress` directly through translator as `rfqProgress`.
- Demo detail/list can calculate lifecycle progress from completed stages and terminal status.
- Blocked and skipped states are displayed.
- The UI must not treat progress as writable; stage progress comes from manager state.

### 15.6 Stage Advancement

Implemented in `RfqOperationalWorkspace` and live-only connector functions.

- UI trigger opens an advance confirmation dialog.
- Before advance, the UI validates commercial numeric fields, approval signature, controlled stage decisions, Go/No-Go selection, and decision-driven blocker reason where those fields are mandatory/current.
- For normal advance, it may first call `updateStage` with captured data/blocker state, then calls `advanceStage`.
- For terminal outcome, it records terminal outcome, lost reason, and outcome reason through captured data and `advanceStage`/cancel flows.
- No-Go cancellation uses the manager cancel endpoint rather than sending `confirmNoGoCancel: true`; tests assert the confirm flag is not present in the component source.
- Success refreshes stage workspace and RFQ detail.
- Errors are displayed in the workspace.
- Stage mutations are disabled in mock mode by connector guard.
- Backend remains authoritative for lifecycle validity.

### 15.7 File Upload / Download

Implemented for stage files in the operational workspace.

- Upload UI uses a native file input in `RfqOperationalWorkspace`; `UploadZone` exists as a reusable demo-style upload component but stage file upload uses `uploadStageFile`.
- Upload target is current RFQ/current stage.
- FormData includes `file` and `type`.
- Success clears selected file and refreshes workspace/detail.
- Download URLs are rendered from translated manager stage files.
- Delete uses `DELETE /files/{fileId}` and role-aware UI checks.
- Accepted file types are not constrained by code in the stage upload handler.
- Mock mode disables live stage file mutation.

### 15.8 Subtasks

Implemented in `RfqOperationalWorkspace`.

- Create requires name, assignee, and due date.
- Due date must fall within the stage window. The window can be planned, actual, or shifted actual based on actual start/end.
- Progress edits cannot move backward once saved.
- Progress derives status: 0 -> Open, 1-99 -> In progress, 100 -> Done.
- Create/update/delete call live manager stage subtask endpoints.
- Mock mode disables stage mutations.

### 15.9 Reminders

Implemented with live-only connectors.

- RFQ workspace can create RFQ-level or stage-linked reminders.
- Reminder due dates cannot be in the past.
- RFQ-level reminder due date must fall between today and RFQ deadline.
- Stage-linked reminder due date must fall inside the current stage window.
- Workspace can resolve reminders.
- Reminder Center is manager-only and can list service-wide reminders, inspect detail, resolve manual reminders, process batch reminders, send a test email, and toggle rules.
- In mock mode, reminder hooks return explicit live-only unavailable errors.

### 15.10 Intelligence Artifacts Display

Implemented in `RFQDetailScreen`, `IntelligencePanel`, `IntelligenceActionsPanel`, and artifact components.

- `useRfqIntelligence` loads snapshot, briefing, workbook profile, workbook review, and artifact catalog in parallel.
- Package intelligence combines snapshot and briefing signals.
- Workbook comparison is gated by `rfq.workbookAvailable`.
- Historical insights are displayed as not mature unless snapshot availability indicates otherwise.
- Staleness notice is derived by comparing manager RFQ `updatedAtValue` with intelligence artifact timestamps.
- Missing resources become partial/unavailable states rather than invented artifacts.
- Actions panel can trigger intake, workbook, and outcome enrichment and request intake/workbook reprocess if role permissions allow.

### 15.11 Theme / Visual Mode

- `ThemeProvider` stores preference in localStorage key `rfq-ui-theme`.
- Modes are `light`, `dark`, and `system`.
- Root layout starts with `className="dark"` and provider applies the resolved class after hydration.
- `ThemeToggle` toggles light/dark.
- Tailwind uses CSS variables from `globals.css`.

## 16. Components Inventory

### Layout / Navigation

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `AppShell` | `src/components/layout/AppShell.tsx` | Dashboard shell composition. | children | Context providers | Indirect through nav. | None confirmed. |
| `Sidebar` | `src/components/layout/Sidebar.tsx` | Primary navigation. | none | navigation config, role context | Filters by role and mock-only featured detail. | UI-only visibility. |
| `TopBar` | `src/components/layout/TopBar.tsx` | Header controls. | none | app shell context | Includes role/theme/connection controls. | None confirmed. |
| `ConnectionIndicator` | `src/components/layout/ConnectionIndicator.tsx` | Shows demo/live backend health. | `compact` | connection context | No role sensitivity. | Health checks use base `/health`, not API prefix. |
| `RoleSwitcher` | `src/components/navigation/RoleSwitcher.tsx` | Local role switcher. | none | role context | All roles. | Not security. |
| `ThemeToggle` | `src/components/navigation/ThemeToggle.tsx` | Theme toggle. | none | theme context | None. | None confirmed. |
| `BreadcrumbTrail` | `src/components/navigation/BreadcrumbTrail.tsx` | Breadcrumbs with RFQ label lookup. | none | `useBreadcrumbs` | RFQ label differs by role. | Breadcrumb fetch can fail silently to generic label. |

### Dashboard

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `DashboardScreen` | `src/components/rfq/DashboardScreen.tsx` | Portfolio dashboard. | none | `useDashboardData` | Executive vs manager layout. | Executive metrics are client-derived. |
| `ExecutiveDistributionCard` | `src/components/rfq/ExecutiveDashboardVisuals.tsx` | Distribution chart-like card. | entries | computed executive insights | Executive-oriented. | No chart library; custom layout. |
| `ExecutiveRankedBarsCard` | same | Ranked bars. | entries | computed executive insights | Executive-oriented. | None confirmed. |
| `LeadershipAttentionQueueCard` | same | Leadership queue. | items | leadership notes/RFQs | Executive-oriented. | Leadership notes demo-only in live connector. |
| `KPICard` | `src/components/common/KPICard.tsx` | KPI display. | metric props | callers | No role logic. | None confirmed. |
| `CircularGauge` | `src/components/common/CircularGauge.tsx` | Animated gauge. | value/label | callers | No role logic. | Pure visual. |

### RFQ List

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `RFQListScreen` | `src/components/rfq/RFQListScreen.tsx` | Queue/monitor screen. | none | `useRfqList` | Role changes title, filters, create CTA. | Query filters can expose views not authorized by backend unless backend enforces. |
| `RFQCard` | `src/components/rfq/RFQCard.tsx` | Card item. | `rfq` | passed model | No direct role logic. | Displays backend/demo state as received. |
| `RFQTable` | `src/components/rfq/RFQTable.tsx` | Table view and sorting. | items | passed models | No direct role logic. | Client-side sorting only. |
| `RFQStatusChip` | `src/components/rfq/RFQStatusChip.tsx` | Status badge. | status | status helpers | No direct role logic. | Must keep live/demo labels separate. |

### RFQ Detail

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `RFQDetailScreen` | `src/components/rfq/RFQDetailScreen.tsx` | Detail shell/tabs. | `rfqId` | manager and intelligence hooks | Tabs depend on role permissions. | Could request intelligence even when resource missing; handled as null/error. |
| `ExecutiveStrategicDetail` | `src/components/rfq/ExecutiveStrategicDetail.tsx` | Executive read-only detail. | RFQ/intelligence/notes | manager/intelligence/leadership | Executive-specific. | Client-derived strategic labels. |
| `LeadershipNotesPanel` | `src/components/rfq/LeadershipNotesPanel.tsx` | Demo leadership note threads. | rfqId, actor, permissions | leadership note connector | Role permissions gate actions. | Live connector unavailable. |

### Workflow / Stage

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `RFQCreateScreen` | `src/components/rfq/RFQCreateScreen.tsx` | Create form and workflow/stage selection. | none | workflow connector, create connector | Create permission required. | Default sample values; demo/live workflow mismatch risk. |
| `RfqOperationalWorkspace` | `src/components/rfq/RfqOperationalWorkspace.tsx` | Live operational stage workspace. | RFQ, permissions, refresh | manager stage/reminder connectors | Strong role gating. | Large component; high regression risk. |
| `RFQStageTimeline` | `src/components/rfq/RFQStageTimeline.tsx` | Stage timeline. | stages | RFQ stage history | No direct role logic. | Must not infer writable progress. |
| `LifecycleProgressStageBox` | `src/components/rfq/LifecycleProgressStageBox.tsx` | Compact lifecycle/progress display. | RFQ/stage props | translated model | No direct role logic. | Display-only. |

### Files / Uploads

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `UploadZone` | `src/components/common/UploadZone.tsx` | Reusable drag/drop-looking upload state component. | title, status, filename | caller controlled | No direct role logic. | Demo-style state; not used as the live stage file uploader. |
| Stage file controls | `src/components/rfq/RfqOperationalWorkspace.tsx` | Upload, list, download, delete stage files. | current stage/RFQ | manager stage file connector | Upload/delete role-scoped. | No explicit accepted-file validation in UI. |

### Reminders

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `ReminderCenterScreen` | `src/components/reminders/ReminderCenterScreen.tsx` | Manager gate for reminder center. | none | role permissions | Manager-only. | UI-only gate. |
| `ReminderCenterPanel` | `src/components/reminders/ReminderCenterPanel.tsx` | Service-wide reminder controls. | permissions | `useReminderCenter` | Manager-only controls. | Live-only. |
| `ReminderCenterSummaryCard` | `src/components/reminders/ReminderCenterSummaryCard.tsx` | Overview reminder stats card. | none | `useReminderSummary` | Manager overview. | Live-only errors in mock. |
| `ReminderDetailDialog` | `src/components/reminders/ReminderDetailDialog.tsx` | Reminder details. | reminder, onClose | passed model | No direct role logic. | Display only. |

### Intelligence

| Component | File path | Purpose | Props if important | Data source | Role sensitivity | Known risks |
|---|---|---|---|---|---|---|
| `IntelligencePanel` | `src/components/intelligence/IntelligencePanel.tsx` | Package/workbook/historical intelligence display. | RFQ and resource states | intelligence hook | Visibility by detail tabs. | Sanitizes some backend phrases; must not hide substantive warnings. |
| `IntelligenceActionsPanel` | `src/components/intelligence/IntelligenceActionsPanel.tsx` | Trigger/reprocess actions. | permissions and callbacks | intelligence triggers/artifacts connector | Manager actions allowed by permissions. | Trigger labels must not imply deterministic success before backend returns. |
| `IntelligenceReadinessBar` | `src/components/intelligence/IntelligenceReadinessBar.tsx` | Readiness visual. | availability/score | caller | No direct role logic. | Display only. |
| `PartialIntelligenceState` | `src/components/intelligence/PartialIntelligenceState.tsx` | Partial/unavailable messaging. | availability | caller | No direct role logic. | Messaging must reflect actual availability. |
| `ArtifactCard` | `src/components/artifacts/ArtifactCard.tsx` | Artifact catalog card. | artifact | artifact catalog | Artifacts tab hidden for executive. | Catalog summaries depend on translator mapping. |

### Shared UI

Local primitives under `src/components/ui` include `button`, `badge`, `card`, `input`, `label`, `progress`, `separator`, `table`, and `textarea`. They are presentation primitives and should remain domain-agnostic.

## 17. State Management

- No Redux/Zustand/global store is present.
- Global UI state uses React contexts: role, theme, toast, connection, app shell.
- Server state is loaded manually in hooks with `useEffect`, `useState`, refresh keys, and connector calls.
- No React Query/SWR cache is present.
- Refresh/invalidation is manual: mutation handlers call `refresh`, `onRfqRefresh`, and hook reload-key increments.
- Form state is local component state.
- Error state is mostly local string state or hook state.
- Toasts are handled by `ToastProvider`.

## 18. Loading, Empty, and Error States

- Loading uses `SkeletonCard` in dashboard, overview, list, detail, workspace, reminders, and intelligence panels.
- Empty and unavailable states use `EmptyState`.
- `http-client.ts` throws `HttpError` with backend `message`, `detail`, response text, or HTTP status fallback.
- Intelligence artifact 404s are intentionally translated to `null`, not hard failures.
- Reminder mock mode returns explicit live-only unavailable messages through hooks.
- Toasts are used for create success, reminder actions, and intelligence action feedback.
- There is no React error boundary file in this repo.
- Retry behavior is manual through refresh buttons in some panels.

## 19. Design System and Styling

- Tailwind CSS is configured in `tailwind.config.ts`.
- Design tokens are CSS variables in `src/app/globals.css`.
- Dark mode uses Tailwind class strategy and is default in root HTML.
- Component primitives are local shadcn-style components built with `class-variance-authority`, `clsx`, and `tailwind-merge`.
- Icons come from `lucide-react`.
- Animation uses `framer-motion` for toasts and some visuals.
- There is no chart library; dashboard visuals are custom React/Tailwind components.
- Branding uses `GHILogo`, `PlatformWordmark`, `ALBASSAM_LOGO.png`, and `public/brand/albassam-logo.png`.
- Visual polish must preserve business truth: progress, statuses, blocked state, intelligence availability, and backend errors must remain visible and not be replaced by decorative states.

## 20. Tests and Validation

| Area | Evidence |
|---|---|
| Test framework | Node `.mjs` scripts using `node:assert/strict`; some transpile TypeScript helpers with local `typescript`. |
| Unit/helper tests | `go-no-go`, `blocker-signal`, workflow selection, subtask/reminder validation, captured-data, formatting. |
| Truth-gate/source tests | `p0-truth-gates`, `p2-demo-isolation`, `intelligence-phase-truth`, `rfq-progress-ui`, `reminder-v1`, `debug-auth-headers`. |
| Component/browser tests | Could not confirm from repository. No Playwright/Jest/Vitest config found. |
| E2E tests | Could not confirm from repository. |
| Build validation | `npm.cmd run build` passed after sandbox escalation allowed Next to spawn workers. |
| Type validation | `npm.cmd run typecheck` passed. |
| Lint validation | `npm.cmd run lint` passed, with Next deprecation warning for `next lint`. |

Exact commands:

```powershell
npm install
npm.cmd run dev
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Get-ChildItem tests -Filter *.test.mjs | Sort-Object Name | ForEach-Object { node $_.FullName }
```

Known test issue:

- Running all tests from `frontend/rfq_ui_ms` failed at `tests/workflow-catalog-truth.test.mjs` because it expects `..\rfq_manager_ms\scripts\bootstrap_base_data.py`, which resolves to `frontend/rfq_manager_ms/...` in this workspace. That sibling path was not present. Excluding that test, the other 11 `.test.mjs` files passed.

## 21. Known Gaps, Risks, and Backlog

| Gap / Risk | Severity | Evidence | Suggested Fix |
|---|---|---|---|
| Role restrictions are UI-only | Important but non-blocking | Role stored in localStorage; no backend auth integration in UI. | Keep backend permission checks authoritative; document UI role gates as presentation only. |
| Public manager token variable | Important but non-blocking | `NEXT_PUBLIC_MANAGER_API_TOKEN` is read and sent as bearer token. | Avoid real secrets; prefer secure server-side auth seam. |
| Debug actor headers can be mistaken for auth | Important but non-blocking | `X-Debug-*` headers enabled by env flag. | Keep disabled by default; label as local/dev only. |
| Reminder mock/live split can surprise users | Nice-to-have | Hooks mark reminders live-only in mock mode. | Keep explicit unavailable messaging; add mock reminders only if backend-equivalent behavior exists. |
| Stage workspace mutation disabled in mock | Nice-to-have | `ensureLiveStageMutationsEnabled` throws. | Keep as-is unless full mock lifecycle simulator is intentionally built. |
| Leadership Notes demo-only | Important but non-blocking | Live connector throws unavailable error. | Add backend API or hide/label live unavailable state. |
| Intelligence portfolio live summary not connected | Nice-to-have | `getIntelligencePortfolioSummary` throws in live mode. | Add backend endpoint or remove unused live seam. |
| Demo/live shape drift | Important but non-blocking | Demo intelligence responses differ from live artifact envelopes. | Add fixture tests for live envelopes and keep translators separate. |
| Test path assumes sibling manager repo under `frontend` | Important but non-blocking | `workflow-catalog-truth.test.mjs` failed in current workspace. | Make path discovery configurable or point to actual manager repo location. |
| No package `test` script | Nice-to-have | `package.json` has dev/build/start/lint/typecheck only. | Add `test` script for existing Node tests. |
| No browser/e2e tests | Important but non-blocking | No Playwright/Jest/Vitest config found. | Add route-level smoke tests for mock and live API modes. |
| File upload accepts any file in UI | Important but non-blocking | Stage upload handler does not enforce accepted types. | Align accepted file constraints with manager backend and show validation. |
| Build initially failed in sandbox with `spawn EPERM` | Already resolved | Escalated `npm.cmd run build` passed. | No code fix needed; document sandbox behavior. |
| `next lint` deprecated | Nice-to-have | Command output says removed in Next.js 16. | Migrate to ESLint CLI before Next 16 upgrade. |
| Hardcoded repro script path | Nice-to-have | `scripts/repro-dev-open-error.mjs` uses `d:/PFE/rfq_ui_ms`. | Parameterize project root. |

## 22. Documentation vs Implementation Drift

| Documented Claim | Actual Implementation | Risk | Suggested Fix |
|---|---|---|---|
| README says mock payloads flow through same boundary. | Mostly true, but stage mutations and reminders are live-only and leadership notes are demo-only. | Agents may expect full mock parity. | Clarify mock/live exceptions in README. |
| README lists connectors/translators/demo architecture. | Code follows this pattern. | Low. | Keep README and this source-of-truth updated together. |
| `.env.example` lists only mock flag, manager URL, intelligence URL, demo latency. | Code also references `NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED` and `NEXT_PUBLIC_MANAGER_API_TOKEN`. | Env setup drift. | Add safe examples/comments for debug vars, warning that token is public. |
| Tests imply manager repo is at `../rfq_manager_ms` relative to UI. | Current workspace did not have `frontend/rfq_manager_ms`. | One test fails in this layout. | Make test path configurable. |
| README says UI consumes both services without duplicating backend business logic. | UI has client-side validation and display derivations, but lifecycle mutations go through manager APIs. | Acceptable if kept presentational/validation-only. | Do not move manager lifecycle truth into UI. |
| No docs directory before this file. | `docs/` was absent during inspection. | Future agents lacked local source-of-truth. | Keep this file current. |

## 23. Rules for Future AI Coding Agents

- Read this file first.
- Inspect the relevant page, component, hook, connector, translator, and model before editing.
- Preserve backend truth boundaries.
- Never hardcode lifecycle state.
- Never invent intelligence artifacts.
- Never mix mock and real data silently.
- Never treat UI role restrictions as security.
- Never change API contracts without checking backend contracts and TypeScript models.
- Never add visual polish that hides status, blocker, readiness, or error truth.
- Never hide backend errors with fake success.
- Never add parser or package/workbook intelligence logic to the UI.
- Never move manager lifecycle rules into frontend helpers.
- Keep mock data behind `NEXT_PUBLIC_USE_MOCK_DATA`.
- Keep demo-only and live-only seams explicit in UI copy and docs.
- Always run lint/typecheck/build/tests before claiming success when feasible.
- Update this source-of-truth file when behavior changes.

## 24. Quick Start

```powershell
cd d:\RFQ_MANAGEMENT_SYSTEM\frontend\rfq_ui_ms
npm install
Copy-Item .env.example .env.local
npm.cmd run dev
```

Run with mock data:

```env
NEXT_PUBLIC_USE_MOCK_DATA=true
NEXT_PUBLIC_MANAGER_API_URL=http://localhost:8000
NEXT_PUBLIC_INTELLIGENCE_API_URL=http://localhost:8001
NEXT_PUBLIC_DEMO_LATENCY_MS=650
```

Run with real backend APIs:

```env
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_MANAGER_API_URL=http://localhost:8000
NEXT_PUBLIC_INTELLIGENCE_API_URL=http://localhost:8001
```

Validation:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Get-ChildItem tests -Filter *.test.mjs | Sort-Object Name | ForEach-Object { node $_.FullName }
```

Swagger/docs:

- Frontend app: `http://localhost:3000` after `npm.cmd run dev`.
- Backend Swagger URLs are not configured in this repo. Could not confirm exact backend docs URLs from repository.

Docker:

```text
Could not confirm exact command from repository.
```

No Dockerfile or compose file was found for this frontend.

## 25. Safe Change Playbooks

### 25.1 Add a New Page

1. Add the route under `src/app`, preferably as a thin page that renders a screen component.
2. Add the screen component under `src/components`.
3. Add navigation only if role visibility is clear in `src/config/navigation.ts`.
4. Load data through hooks/connectors, not directly in deeply nested presentational components.
5. Add loading, empty, and error states.
6. Add or update truth-gate/component tests.

### 25.2 Add a New API Call

1. Add or update TypeScript DTOs in `src/models`.
2. Add connector function in `src/connectors/manager` or `src/connectors/intelligence`.
3. Add translator function in `src/translators` if UI shape differs from API shape.
4. Add mock equivalent only behind `NEXT_PUBLIC_USE_MOCK_DATA`.
5. Surface errors through hook/component state.
6. Add tests that cover mock/live separation and contract mapping.

### 25.3 Add a New RFQ Field to the UI

1. Confirm the field exists in `rfq_manager_ms` response/request contracts.
2. Update `src/models/manager/api-rfq.ts` and UI models in `src/models/manager/rfq.ts`.
3. Update manager translators.
4. Update display components or forms.
5. Update create/update payloads only if backend supports writes.
6. Update demo data and tests without inventing backend truth.

### 25.4 Change Role-Based UI Behavior

1. Update capability definitions in `src/config/role-capabilities.ts`.
2. Update derived booleans in `src/config/role-permissions.ts` if needed.
3. Update navigation and component action visibility.
4. Keep backend permission checks authoritative.
5. Add tests for role-specific visibility or source truth.

### 25.5 Add a New Dashboard KPI

1. Prefer a backend endpoint from `rfq_manager_ms` or `rfq_intelligence_ms`.
2. Add connector/model/translator support.
3. Add mock data with matching semantics.
4. Render through KPI/shared components.
5. Show unavailable state instead of fake values when data source is missing.

### 25.6 Add a New Intelligence Panel

1. Confirm artifact or endpoint exists in `rfq_intelligence_ms`.
2. Add artifact content type under `src/models/intelligence`.
3. Add connector and translator.
4. Define missing/partial/stale behavior.
5. Add UI component and role visibility.
6. Add tests for no-artifact and partial-artifact states.

### 25.7 Change File Upload UI

1. Confirm accepted file constraints and endpoint behavior in `rfq_manager_ms`.
2. Update UI accepted types and validation.
3. Keep FormData keys aligned with backend (`file`, `type` for current stage upload).
4. Preserve upload loading/error/success refresh behavior.
5. Test role restrictions and backend error display.

### 25.8 Update Mock Data

1. Keep mock changes inside `src/demo`.
2. Preserve mock/live branch separation in connectors.
3. Update translators only when shape mapping changes.
4. Avoid adding demo-only states to live status helpers.
5. Update truth-gate tests when mock shape changes intentionally.

## 26. Final Architectural Verdict

`rfq_ui_ms` has a clear frontend architecture: thin routes, screen components, connector boundaries, translators, typed models, and explicit mock/live configuration. Its strongest parts are the service-boundary awareness, role-aware UI presentation, and careful handling of intelligence availability as partial or missing instead of invented.

The fragile areas are the large operational workspace component, demo/live schema drift, local-only role gating, and partial seams such as demo-only leadership notes, live-only reminders, and live-only stage mutations. The most important thing to protect is the truth boundary: manager owns lifecycle and permissions, intelligence owns derived artifacts, and UI only displays or invokes backend contracts.

Best next improvement: add a proper `npm test` script and fix the manager-workflow test path so all truth-gate tests pass reliably in this workspace layout.
