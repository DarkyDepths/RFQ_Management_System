# Scope Discipline Rules

## Purpose

This file defines the wording discipline that must be preserved when transforming the report from v0 to v1.

The report must be ambitious but honest. It must clearly distinguish what is implemented, what is validated, what is partial, what is only architecturally specified, and what is future work.

## Dynamic status rule

The report remains flexible until the final submission date.

Implementation status may evolve during the remaining development period. A capability that is currently partial, validation pending, or future may become implemented and tested before submission.

Therefore, every status label must be understood as valid at the time of the latest evidence snapshot, not as a permanent classification.

When updating the report, always use the most recent verified evidence:

1. Current code and tests.
2. Latest implementation audit.
3. Latest validation audit.
4. Latest confirmed demo or supervisor/client validation.
5. Older documents only if still aligned with the current code.

If a capability improves before submission, its wording may be upgraded, but only after evidence exists.

Examples:

- If copilot-intelligence integration becomes implemented and tested, it can move from "deferred/future" to "implemented and tested".
- If frontend browser E2E tests are added and pass, UI validation can be upgraded from "manual/demo" to "implemented and tested".
- If manager tests are run successfully against PostgreSQL, the previous SQLite-only caveat should be updated.
- If Postman/Newman execution logs are produced, Postman validation can be reported as executed rather than only structured.

The rule is: never underclaim outdated limitations, but never overclaim future intent.

## Status labels

Use these labels consistently when describing capabilities.

### implemented and tested

Use when the capability exists in code and is covered by passing automated tests or reproducible validation evidence.

Safe wording:

- "The service implements..."
- "The test suite validates..."
- "This capability is implemented and tested..."

### implemented, validation pending

Use when the capability exists in code but complete validation evidence is not available.

Safe wording:

- "The service implements..., with validation pending."
- "The implementation provides..., subject to further validation."

### partial

Use when part of the capability exists but the full target behavior is not complete.

Safe wording:

- "The current implementation provides partial support for..."
- "This capability is available at foundation level..."

### demo/mock

Use when the capability is available for demonstration or UI continuity but not as a production-grade implementation.

Safe wording:

- "A demonstration implementation provides..."
- "This is available in demo mode..."
- "The UI supports this through mock/demo data..."

### documented only

Use when the capability is described in architecture or docs but not found in code.

Safe wording:

- "The architecture specifies..."
- "The design anticipates..."
- "This remains a documented architectural direction..."

### deferred/future

Use when the capability is intentionally outside the current scope.

Safe wording:

- "This capability is deferred to future work."
- "This belongs to the future scope of the platform."
- "This is part of the long-term vision, not the present implementation."

### not found / unclear

Use when the repository or documents do not provide enough evidence.

Safe wording:

- "No implementation evidence was found."
- "The current evidence is insufficient to claim..."
- "This point requires confirmation."

## Claims to avoid

Do not claim:

- full production readiness,
- full UI browser E2E validation,
- full IAM/SSO implementation,
- full copilot-intelligence integration,
- autonomous manager-intelligence event-bus integration,
- live Azure OpenAI validation in CI,
- Postgres-level manager validation if only SQLite was used,
- full Postman execution if only the collection exists,
- all tests pass globally if some service tests are partial or fixture-dependent,
- predictive intelligence if only parsing foundation is implemented,
- long-term episodic memory if only working memory capture exists.

## Preferred framing

The report should present the project as:

- a strong operational RFQ lifecycle backbone,
- a trust-bound AI copilot as the main innovation,
- a parsing/intelligence foundation,
- a UI integration surface,
- a platform with clear future extension paths.

## Main narrative to protect

The report must preserve this narrative:

Audit revealed that BOQ automation was unsafe and infeasible under current data conditions. The project therefore pivoted to RFQ lifecycle intelligence. The platform provides a structured lifecycle backbone, evidence-grounded conversational assistance, and a foundation for future intelligence.

---

## Reconciliation note (2026-05-10)

This file remains the authoritative source for the seven status labels and the foundational scope-honesty discipline.

The operational layer that applies these labels per chapter, plus the wording-softening rules accumulated across the eleven amendment rounds of the v0 → v1 transformation, lives in:

- `cross_chapter_wording_rules_v1.md` — naming canon (N-1 to N-4) · wording-softening rules (W-1 to W-8) · content-placement rules (P-1 to P-8) · structural rules (S-1 to S-8) · bibliography rule B-1 · acceptance rule A-1
- `chapter_checklists_v1.md` — six chapter must-not-be-lost checklists (Ch 1, Ch 2 v1 SoA, Ch 3, Ch 4, Ch 5, Ch 6) with verification procedures

The "Claims to avoid" list in this file (full production readiness, full UI E2E, full IAM/SSO, full copilot-intelligence integration, autonomous manager-intelligence event-bus, live Azure OpenAI in CI, Postgres-level manager validation, full Postman execution, all-tests-pass globally, predictive intelligence, long-term episodic memory) is preserved verbatim and is the rule source for content-placement rules P-1 through P-8 in `cross_chapter_wording_rules_v1.md`.