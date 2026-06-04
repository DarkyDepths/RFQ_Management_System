# Validation Evidence Report — Current Evidence Snapshot

This file summarizes the validation evidence found in the repository at the time of the audit.

Important: this is a current evidence snapshot, not a permanent final state. If tests, CI, Postman/Newman runs, browser E2E tests, PostgreSQL validation, or live LLM validation are added before submission, this file should be updated or superseded by a newer validation audit.

RFQ Management System — Validation Evidence Report
This report is based on direct inspection of the repository at d:/RFQ_MANAGEMENT_SYSTEM (branch feat/rfq-copilot-batch10-v2-threads-working-memory). Where I report a pass/fail count, I also state the exact command I ran and from which directory. No code was modified.

Important runtime caveat: I executed the Python test suites against the shared D:\RFQ_MANAGEMENT_SYSTEM\.venv interpreter, not against per-service Docker containers. The manager service was therefore exercised against an in-memory SQLite database (via DATABASE_URL=sqlite:///./.qg.db), not the Postgres production target. Schema-specific Postgres behavior (e.g. JSONB query semantics, actual_end indexing) was not exercised by my run. Reported pass counts apply to the SQLite invocation.

1. Manager service validation
Test framework: pytest (microservices/rfq_manager_ms/pytest.ini).
Test files: 27 Python files under tests/unit/ (25 files) and tests/integration/ (2 files).
Tests collected: 259 tests (pytest --collect-only -q reports 259 tests collected).
Coverage areas (by test filename):
RFQ CRUD / lifecycle: test_rfq_controller.py (29 tests), test_rfq_lifecycle.py (3), test_rfq_by_code_endpoints.py (16), test_rfq_datasource_sort.py (3), test_rfq_datasource_analytics.py (3).
Workflow: test_workflow_controller.py (6).
Stages, mandatory fields, blockers, notes: test_rfq_stage_controller.py (68 tests — the largest file).
Subtasks: test_subtask_controller.py (19).
Files: test_file_controller.py (10) + integration test_fs01_file_roundtrip.py (3).
Reminders: test_reminder_controller_actor_attribution.py (11), test_reminder_translator.py (2).
Auth: test_auth_enforcement.py (13), test_auth_actor_propagation.py (3), test_iam_service_connector.py (3), test_app_auth_bypass.py (3).
Observability / pagination / settings: test_observability_baseline.py (9), test_pagination.py (5), test_settings_fail_fast.py (3).
Code generation: test_rfq_code_generation_atomic.py (3).
Event bus, notification, dormant H5 model decisions: test_event_bus_connector.py (3), test_notification_service.py (7), test_h5_dormant_model_decisions.py (2).
Scenario seed / runtime sync / API integration: test_rfqmgmt_scenario_seed.py (13), test_seed_runtime_sync.py (3), integration test_api_layer.py (15).
One-command runner: yes — scripts/verify.py chains ruff lint → pytest → app import. Same script is used by CI.
Pass/fail evidence (reproducible by me during this audit):
Command: cd microservices/rfq_manager_ms; DATABASE_URL=sqlite:///./.qg.db PYTHONPATH=. python -m pytest -q --tb=no.
Result: 259 passed, 121 warnings in 25.29s. (Ruff lint, also part of verify.py, was not run in this audit.)
Postman collections: two JSON files at docs/postman/ — rfq_manager_ms_postman_full_walkthrough_v2.json and its env file. Collection has Folder 0 / Folder 1 demo storyline with auto-bootstrapped variables. Collection exists, execution status not confirmed in this repo (no Newman run logs, no exported run reports).
Demo / walkthrough scripts: scripts/rfqmgmt_scenario_stack.py (top-level), microservices/rfq_manager_ms/scripts/seed_rfqmgmt_scenarios.py, docs/SMOKE_DEMO.md (PowerShell + Bash smoke recipe), docs/RUNBOOK.md. Manifest artifacts for past seed runs are checked in at seed_outputs/.
CI: microservices/rfq_manager_ms/.github/workflows/ci.yml — runs python scripts/verify.py on push/PR to main against Python 3.11 with DATABASE_URL=sqlite:///./.quality_gate.db. No CI run logs are committed to this repo; status badges or recorded run outputs are not present in the working tree.
Validation gaps:
All my run + the CI workflow use SQLite; Postgres-specific behavior is not exercised by automated tests.
The Postman collection has not been Newman-run as part of CI; no recorded execution.
Concurrency hardening for LG-06 (RFQ code generation) is flagged as deferred (RELEASE_v1.0.0.md:21).
Stats/analytics fields avg_margin_*, estimation_accuracy are returned as None and are not validated (because there is nothing to validate yet — src/datasources/rfq_datasource.py:318-323).
2. Copilot service validation
Test framework: pytest with asyncio_mode=auto (microservices/rfq_copilot_ms/pytest.ini).
Test files: 47 Python files across tests/anti_drift/, tests/config/, tests/controllers/, tests/datasources/, tests/docs/, tests/models/, tests/pipeline/, tests/smoke/.
Tests collected: 636 tests (pytest --collect-only -q reports 636 tests collected in 4.27s).
Pipeline coverage (each stage has at least one dedicated test file in tests/pipeline/):
FastIntake → test_fast_intake.py.
Planner → test_planner.py.
PlannerValidator → test_planner_validator.py.
ExecutionPlanFactory → test_execution_plan_factory.py.
Resolver → test_path4_resolver.py.
Access → test_path4_access.py.
ToolExecutor → test_tool_executor_path4.py.
EvidenceCheck → test_evidence_check_path4.py.
ContextBuilder → test_context_builder_path4.py.
Compose → test_compose_path4.py.
Guardrails → test_guardrails.py.
Judge → test_judge_path4.py.
Finalizer → test_finalizer.py.
EscalationGate → test_escalation_gate.py.
Persist → test_persist_execution_records.py.
Path 4 deterministic renderer → test_path4_renderer.py.
Pipeline file count: 216 test functions in tests/pipeline/.
Anti-drift CI guards (tests/anti_drift/, 18 functions):
test_no_turn_execution_plan_outside_factory.py — only ExecutionPlanFactory may construct TurnExecutionPlan.
test_path_registry_reader_allowlist.py — only factory + gate may import the runtime PATH_CONFIGS.
test_fast_intake_anchored.py — FastIntake regex must use anchored full-match.
test_no_llm_sdk_in_deterministic_stages.py — no LLM SDK imports in deterministic stages.
test_llm_structured_output_enforced.py — Planner / Compose / Judge must request structured output.
test_no_v3_references.py — no source references to superseded v3 architecture.
test_memory_policy_load_bearing.py — memory policy is read where required.
test_batch10_no_history_injection.py — batch 10 must NOT inject working memory into Planner / Compose / Judge prompts.
Smoke tests (tests/smoke/, 98 functions):
v1 lane preserved → test_v1_preserved.py.
v2 thread lifecycle → test_v2_threads_lifecycle.py, test_v2_thread_ownership_enforcement.py, test_v2_turn_requires_known_thread.py.
v2 turn (Path 4 flows) → test_v2_path4_manager_core.py, test_v2_path4_by_code_integration.py, test_v2_path4_compose_judge.py, test_v2_template_slice.py.
v2 guardrails / persistence / app readiness → test_v2_guardrails.py, test_v2_execution_records.py, test_v2_slice1_app_readiness.py.
LLM-unavailable / Path 8.5 graceful fallback → test_v2_returns_501.py (file name is historical; it now tests the Path 8.5 graceful path).
Path coverage:
Path 1 (greetings/templates): tested via FastIntake tests + smoke test_v2_returns_501.py::test_fast_intake_messages_still_work_when_planner_unavailable.
Path 4 (RFQ-grounded): full chain tested in pipeline + smoke.
Path 8.x (safe templates): tested via escalation gate and smoke (e.g. test_v2_returns_501.py::test_non_fast_intake_message_routes_to_path_8_5_when_planner_unavailable).
Paths 2/3/5/6/7 (deferred): anti-drift / factory tests verify they route to safe Path 8 fallbacks (src/config/path_registry.py:38-43 — the unsupported_intent_topic rule is asserted by test_execution_plan_factory.py).
Working memory:
Capture is tested → tests/pipeline/test_working_memory_capture.py.
Non-injection (Batch 10 boundary) is tested → tests/anti_drift/test_batch10_no_history_injection.py.
Eval datasets / golden CSVs: none found. No *.csv or *.jsonl evaluation datasets exist anywhere in the copilot service (find ... -name "*.csv" -o -name "*.jsonl" returns nothing). LLM-stage tests use FakeLlmConnector with hand-coded JSON response queues (e.g. tests/smoke/test_v2_path4_compose_judge.py:8-17).
Pass/fail evidence (reproducible by me during this audit):
Command: cd microservices/rfq_copilot_ms; PYTHONPATH=. python -m pytest -q --tb=no.
Result: 636 passed, 3 warnings in 4.84s.
The .pytest_cache/v/cache/lastfailed file (microservices/rfq_copilot_ms/.pytest_cache/v/cache/lastfailed) lists 5 historical failures whose test names no longer exist in the source files (they were renamed in the slice-1 cutover, e.g. test_v2_returns_501_for_non_fast_intake_message → test_non_fast_intake_message_routes_to_path_8_5_when_planner_unavailable). The cache is stale; my run shows all current tests passing.
Validation gaps:
No LLM-prompted golden-answer dataset for Path 4 quality measurement; LLM stages run only against fakes.
No measurement of judge agreement / pass rate against a benchmark set.
No runtime test against a real Azure OpenAI deployment in CI; the LLM is always mocked.
No CI workflow file for the copilot service in this repo (only manager has CI).
Alembic migration directory is empty; schema is bootstrapped via Base.metadata.create_all — there is no migration upgrade/downgrade test.
3. Intelligence service validation
Test framework: pytest (microservices/rfq_intelligence_ms/pytest.ini).
Test files: 39 Python files (12 in tests/package_parser/, 17 in tests/workbook_parser/, 10 at the tests/ root).
Tests collected: 118 tests (pytest --collect-only -q after I installed openpyxl xlrd python-docx into the shared venv — those parser deps were missing locally even though they are in requirements.txt).
Coverage:
MR-package parser (22 functions in tests/package_parser/): test_zip_scanner.py, test_tree_scanner.py, test_section_classifier.py, test_identity_extractor.py, test_bom_extractor.py, test_standards_extractor.py, test_compliance_extractor.py, test_sa175_extractor.py, test_rvl_extractor.py, test_cross_checks.py, test_parser_orchestrator_e2e.py.
Workbook parser (46 functions in tests/workbook_parser/): readers (test_workbook_reader_smoke.py), template matcher (test_template_match_smoke.py, test_template_matcher_unit.py), extractors (test_top_sheet_extractor.py, test_general_extractor.py, test_boq_extractor.py, test_bid_s_extractor.py, test_cash_flow_extractor.py, test_mat_breakup_extractor.py), cross-checks (test_cross_checks.py), orchestrator (test_parser_orchestrator_e2e.py, test_parser_pack2_*.py), batch seed runner (test_batch_seed_runner*.py, test_batch_seed_run_summary_record.py).
Cross-check / anomaly tests: tests/package_parser/test_cross_checks.py and tests/workbook_parser/test_cross_checks.py. They reference run_identity_cross_checks, run_numeric_cross_checks, run_cash_flow_cross_checks, run_mat_breakup_cross_checks, run_boq_cross_checks from src/services/workbook_parser/cross_checks.py.
Briefing: tests/test_briefing_service.py.
Routes / smoke / health: tests/test_routes_smoke.py, tests/test_health.py, tests/test_artifact_invariants.py, tests/test_batch_seed_run_read_routes.py.
Lifecycle flows: tests/test_rfq_created_flow.py, tests/test_workbook_uploaded_flow.py, tests/test_outcome_recorded_flow.py.
Snapshot / intake / scenario seed: tests/test_snapshot_service.py, tests/test_intake_service.py, tests/test_rfqmgmt_scenario_seed.py.
Golden reference fixtures: tests reference real artifacts — SA-AYPP-6-MR-022_COLLECTION VESSEL - CDS-REV-00 (test_parser_orchestrator_e2e.py:8; referenced in 11 package-parser test files) and IF-25144 workbook (ghi_workbook_32_sheets.xls — test_top_sheet_extractor.py:14; referenced in 7 workbook-parser test files). These fixtures live under tests/local_fixtures/ which is gitignored (.gitignore:47-48) and not present in the checkout I audited. The same archive (SA-AYPP-6-MR-022_COLLECTION_VESSEL.zip) is also present as an upload in microservices/rfq_manager_ms/uploads_scenario/ (committed).
Fixtures vs. mocked data: tests are written to operate against the real artifacts (real .xls, real ZIP, real BOM workbook). When the fixtures are missing they raise FileNotFoundError rather than fall back to mocks.
Pass/fail evidence (reproducible by me during this audit, after pip install openpyxl xlrd python-docx):
Command: cd microservices/rfq_intelligence_ms; PYTHONPATH=. python -m pytest -q --tb=no.
Result: 48 failed, 64 passed, 6 skipped, 2 warnings in 1.42s.
All 48 failures are FileNotFoundError for files under tests/local_fixtures/... (e.g. the workbook ghi_workbook_32_sheets.xls, the package root). Verified by re-running one failure: test_top_sheet_extractor.py:25 raised FileNotFoundError: Workbook file not found: ...local_fixtures/workbook_uploaded/workbook_sample_001/ghi_workbook_32_sheets.xls.
In other words: the 64 fixture-independent tests passed; the 48 fixture-dependent tests failed because the gitignored fixture directory is not part of the repository. The tests themselves are real and run real parser code; they just need the artifact set committed elsewhere or fetched.
Validation gaps:
The repository on its own cannot demonstrate the parser works against a real RFQ package because the local_fixtures/ directory is gitignored. Any reproducer must obtain or place the SA-AYPP-6-MR-022 package and IF-25144 workbook locally.
briefing_service.py and intake_service.py are documented as "partially implemented" (briefing_service.py:13, intake_service.py:11-12); their tests cover what is currently implemented.
No CI workflow exists for the intelligence service in this repo.
requirements.txt is not enforced by CI/lockfile in a way visible here (parser libs were missing from the shared venv).
4. Frontend / UI validation
Test framework: Node-native assert/strict (node tests/<file>.test.mjs). No Playwright, Cypress, Jest, Vitest, React Testing Library, or any browser-driving framework — verified by grepping package.json (frontend/rfq_ui_ms/package.json) and searching for playwright|cypress|jest|vitest (no matches outside node_modules).
Test files: 12 .mjs scripts under frontend/rfq_ui_ms/tests/ — blocker-signal, debug-auth-headers, go-no-go, intelligence-phase-truth, p0-truth-gates, p2-demo-isolation, p2-executive-insights, reminder-v1, rfq-progress-ui, stage-workspace-phase4, workflow-catalog-truth, workflow-custom.
Test nature: each script readFiles .ts/.tsx source files and asserts that specific string/contract patterns are present (e.g. tests/p0-truth-gates.test.mjs:5-50 reads src/config/api.ts, src/connectors/manager/rfqs.ts, etc.). These are source-contract tests, NOT real UI E2E tests. No browser is launched; no API is called.
Pass/fail evidence (reproducible by me during this audit):
Command: per-file node tests/<file>.test.mjs (no test runner configured; package.json has no test script).
Result: 11 of 12 PASSED. 1 FAILED: tests/p0-truth-gates.test.mjs — AssertionError [ERR_ASSERTION] at line 83. The assertion expects navigation.ts to contain the literal string 'const showFeaturedDetail = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";'; the current source file does not contain that exact line. This is drift between the contract test and the actual source — not a runtime bug.
UI screen validation: there is no automated browser/UI test, so the UI screens themselves are validated only manually (per the docs/SMOKE_DEMO.md flow that says cd ../rfq_ui_ms; npm run dev). Authentication has no UI flow at all (role is localStorage).
Validation gaps:
No browser end-to-end test framework is configured.
No screenshot, recording, or visual regression artifact in the repo.
The contract tests that do exist are not invoked by any npm test script — they are run manually.
One contract test currently fails on this branch (drift).
5. Integration validation
Edge	Evidence
UI → manager	Implemented (connectors at src/connectors/manager/). Validation: only the source-contract tests above (which check that the connectors call the right URLs / shapes); no E2E test calls a running manager service from a running UI. The Postman collection covers the manager API directly, not via the UI.
UI → copilot	Implemented (src/connectors/copilot/threads.ts — turns hit /v2, lifecycle hits /v1). Validation: source-contract tests only. No E2E.
UI → intelligence	Implemented (src/connectors/intelligence/). Validation: source-contract tests only. No E2E.
Copilot → manager	Implemented + tested. Pipeline tests use a real FakeManagerConnector simulating manager responses; smoke tests in tests/smoke/test_v2_path4_manager_core.py and test_v2_path4_by_code_integration.py drive the full /v2 turn through the copilot pipeline against a fake manager. No test runs the copilot against a live manager service.
Manager → intelligence	Manager publishes events to EVENT_BUS_URL; intelligence has lifecycle handlers for rfq.created / workbook.uploaded / outcome.recorded. The handlers are unit-tested in test_rfq_created_flow.py, test_workbook_uploaded_flow.py, test_outcome_recorded_flow.py — but with mocked events, not via the actual event bus. The repo per src/event_handlers/lifecycle_handlers.py:22-26 explicitly states "operational for manual-trigger and direct-handler flows; not yet wired to an autonomous event bus consumer."
Copilot → intelligence	Not implemented. INTELLIGENCE_BASE_URL is declared in src/config/settings.py:31 but never read by code. Therefore not validated and cannot be validated.
Full E2E demo	scripts/rfqmgmt_scenario_stack.py brings up manager + intelligence Postgres + APIs via Docker Compose with seed data (all --seed-set full). docs/SMOKE_DEMO.md is a manual PowerShell/Bash recipe for a smoke walkthrough; the doc text says "Postman Validation Order (Validated)" and "Validated local V1 proof now covers …" — but those are claims by the doc author, not artifacts of an automated run captured in the repo. Past seed manifests exist at seed_outputs/rfqmgmt_manager_manifest.json and [seed_outputs/rfqmgmt_intelligence_manifest.json](seed_outputs/rfqmgmt_intelligence_manifest.json), plus per-RFQ uploaded files at microservices/rfq_manager_ms/uploads_scenario/.
Logs / screenshots / recordings	Only .next-dev.{out,err}.log from a frontend dev session at frontend/rfq_ui_ms/. No demo recording, no screenshot directory.
6. Chapter 5 usable results
Validation area	Evidence found	Status	Safe wording for the report
Manager unit/integration tests	259 tests collected; my run on this branch: 259 passed against SQLite (cmd: pytest -q --tb=no from microservices/rfq_manager_ms)	validated and passing (SQLite)	"The manager test suite collects and passes 259 tests against the SQLite quality-gate target used by the CI workflow."
Manager — Postgres validation	Only SQLite is exercised by tests + CI	validation exists, run status unconfirmed	"An equivalent Postgres-targeted validation run is to be reported in Chapter 5."
Manager — Postman walkthrough collection	Two JSON files at docs/postman/; scripts inside use pm.test(...) assertions	validation exists, run status unconfirmed	"A Postman walkthrough collection exists for the manager API; its execution results are to be reported in Chapter 5."
Manager CI	microservices/rfq_manager_ms/.github/workflows/ci.yml; no run logs in repo	validation exists, run status unconfirmed	"A continuous integration workflow exists for the manager service; recorded run results are not embedded in the repository."
Manager — verify.py (lint + tests + import)	scripts/verify.py; only the pytest step was reproduced in this audit	validation exists, run status unconfirmed (lint not reproduced)	"A single-command quality verification entry point exists; pytest results are reproduced in Chapter 5."
Copilot pipeline stage tests	216 functions across tests/pipeline/; my run: 636 passed overall (cmd: pytest -q --tb=no from microservices/rfq_copilot_ms)	validated and passing	"The copilot test suite validates each pipeline stage and passes 636 tests in total."
Copilot anti-drift CI guards	8 tests in tests/anti_drift/; part of the same passing run	validated and passing	"Anti-drift guard tests are present and pass."
Copilot v2 thread + turn smoke	98 functions in tests/smoke/; part of the same passing run	validated and passing	"Smoke tests cover thread lifecycle, ownership enforcement, and Path 4 turn flows."
Copilot Path 1 / Path 4 / Path 8.x routing	Pipeline + smoke tests above	validated and passing	"Path 1, Path 4, and Path 8.x routing are exercised by smoke and pipeline tests."
Copilot deferred Paths 2/3/5/6/7 fallback	test_execution_plan_factory.py exercises the F1 unsupported-intent rule; routing to Path 8 is asserted by the factory tests	validated and passing	"The factory rule that maps unsupported paths to safe Path 8 templates is validated by automated tests."
Copilot working-memory capture	tests/pipeline/test_working_memory_capture.py; part of the same passing run	validated and passing	"Working-memory capture is validated by dedicated tests."
Copilot working-memory non-injection	tests/anti_drift/test_batch10_no_history_injection.py; part of the same passing run	validated and passing	"An explicit anti-drift test verifies that working memory is not yet injected into Planner/Compose/Judge prompts."
Copilot LLM eval datasets / golden answers	None found	not validated / not found	"No automated grading dataset for LLM-stage answer quality was found in the repository; this is acknowledged as a limitation."
Copilot live LLM testing	LLM connectors are always mocked in tests	manual/demo validation only	"Live Azure-OpenAI integration is exercised through manual demonstration only."
Copilot CI	No workflow file exists	not validated / not found	"No continuous-integration pipeline is configured for the copilot service in this repository."
Intelligence — fixture-independent tests	64 of 118 collected tests pass when fixtures are absent	validated and passing	"Sixty-four fixture-independent intelligence tests pass on a clean checkout."
Intelligence — fixture-dependent tests (real artifacts: SA-AYPP-6-MR-022, ghi_workbook_32_sheets.xls)	48 tests reference real fixtures under gitignored tests/local_fixtures/; all 48 raise FileNotFoundError when those artifacts are missing	validation exists, run status unconfirmed (without fixtures)	"Forty-eight tests are designed to run against real RFQ packages and workbooks held outside the repository; reproducing them requires obtaining the reference fixtures."
Intelligence — cross-checks / anomaly	tests/package_parser/test_cross_checks.py and tests/workbook_parser/test_cross_checks.py (failed in my run because they need the fixtures)	validation exists, run status unconfirmed (without fixtures)	"Cross-check tests exist and become executable once the reference fixtures are placed locally."
Intelligence — briefing / intake / snapshot services	Dedicated files: test_briefing_service.py, test_intake_service.py, test_snapshot_service.py (mostly fixture-free; passed in my run)	validated and passing	"The briefing, intake, and snapshot services are exercised by automated tests, which pass on a clean checkout."
Intelligence — manager-event handlers (rfq.created, workbook.uploaded, outcome.recorded)	tests/test_rfq_created_flow.py, tests/test_workbook_uploaded_flow.py, tests/test_outcome_recorded_flow.py. One workbook-flow test failed in my run (template-mismatch path requires the fixture)	validation exists, run status unconfirmed (one fixture-dependent failure)	"Lifecycle handlers are validated by automated tests; one workbook-flow assertion depends on the gitignored fixture set."
Intelligence CI	No workflow file exists	not validated / not found	"No continuous-integration pipeline is configured for the intelligence service."
Frontend contract tests	12 .mjs scripts; my per-file run on this branch: 11 passed, 1 failed (p0-truth-gates.test.mjs line 83 assertion drift)	partial — validation exists, currently failing on drift	"Twelve source-contract scripts cover the frontend. Eleven currently pass; one (p0-truth-gates.test.mjs) currently fails because of drift between the contract assertion and the source file."
Frontend browser E2E	None — no Playwright / Cypress / Jest setup	not validated / not found	"No automated browser end-to-end test suite is present; UI screens are validated by manual demonstration."
Frontend authentication / login flow	None — role is local-storage, no login UI	not applicable	"An end-user authentication flow is not in scope for the current build, so no validation is required."
UI ↔ manager / UI ↔ copilot / UI ↔ intelligence E2E	No browser-driven test in repo	not validated / not found	"Cross-service flows from the UI are exercised by manual demonstration only."
Copilot ↔ manager (test-double)	12 smoke tests in tests/smoke/ drive full /v2 turns through the copilot against FakeManagerConnector	validated and passing	"Copilot–manager interaction is validated end-to-end through the copilot pipeline against a faked manager connector."
Copilot ↔ manager (live)	No live integration test	manual/demo validation only	"Live copilot–manager calls are exercised through manual demonstration only."
Copilot ↔ intelligence	Integration not implemented	not applicable	"This integration is not implemented; therefore no validation is expected at this stage."
Manager ↔ intelligence (event bus, autonomous)	Documented as not yet wired	not validated / not found	"The autonomous event consumer is acknowledged as future work and is therefore not validated."
Full-stack scenario stack	scripts/rfqmgmt_scenario_stack.py; seed manifests in seed_outputs/; SMOKE_DEMO recipe	manual/demo validation only	"An end-to-end scenario stack and accompanying smoke recipe exist; their execution is reported as a manual demonstration."
Reproducible test artefacts in repo	.pytest_cache/lastfailed (stale), seed manifests, scenario uploads, .next-dev.*.log	partial / advisory	"The repository ships seed manifests and scenario uploads. No JUnit XML, coverage report, or recorded test-run log is committed."
7. Final warnings — claims to avoid in the report
Use these only as guard-rails; do not state them as conclusions:

Do not claim full browser end-to-end UI validation. Frontend tests are 12 Node assert/strict source-contract scripts. There is no Playwright, Cypress, Jest, Vitest, or React Testing Library setup, and no npm test script. One of those contract scripts currently fails.
Do not claim "all tests pass" globally. Three caveats:
Intelligence: 48 of 118 tests fail on a clean checkout because their gitignored real-artifact fixtures (tests/local_fixtures/...) are absent. They are not bug-failures; they are environment-dependency failures.
Frontend: 1 of 12 contract scripts (tests/p0-truth-gates.test.mjs) currently fails on this branch.
Stale pytest caches list test names that no longer exist; do not cite lastfailed as evidence of current state.
Do not claim copilot–intelligence integration validation. The integration is not implemented in code; there is nothing to validate.
Do not claim manager–intelligence event-bus integration is validated end-to-end. The intelligence service explicitly states it has no autonomous event-bus consumer; cross-service event flow is exercised by manual triggers.
Do not claim Postgres-level validation for the manager. Both my run and the CI workflow use SQLite. Postgres-only behaviors (JSONB, indexes, concurrency under load) are not exercised by the automated suite.
Do not claim the Postman collection has been executed in CI. The collection file is committed; no Newman run logs, no exported Postman run reports, and no CI step that runs Newman exist in the repo.
Do not claim live Azure-OpenAI integration is automatically tested. All Planner / Compose / Judge tests use a FakeLlmConnector. Live LLM behavior is exercised only through manual demonstration.
Do not claim copilot answer-quality is validated against a benchmark. No CSV / JSONL / golden-answer dataset for path classification, field grounding, or escalation routing exists in the repo.
Do not claim concurrency-safe RFQ code generation. RELEASE_v1.0.0.md:21 lists LG-06 as deferred. The atomicity test exists but the limitation is acknowledged.
Do not claim the SMOKE_DEMO doc constitutes automated validation. It is a manual recipe; the "(Validated)" labels in that doc are author claims, not committed test artifacts.
Do not claim CI coverage across all services. Only the manager service has a .github/workflows/ci.yml; copilot, intelligence, and frontend have no CI workflow file in this repo.
Do not claim the intelligence parser was validated against IF-25144 and SA-AYPP-6-MR-022 on this branch. The tests reference those artifacts but the artifacts are not in the repo, so without externally provisioning the fixtures the parser-vs-real-artifact assertion remains unverified in this checkout