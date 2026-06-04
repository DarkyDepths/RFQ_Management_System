# Cross-Chapter Wording Rules Registry v1

**Status:** Authoritative consolidation of all wording rules accumulated across the eleven amendment rounds of the v0 → v1 transformation work.
**Created:** 2026-05-10
**Owner:** Mohamed Guidara (project author); rules accumulated in collaboration with Claude Code through Ch 1 reconciliation, Ch 3 v1, Ch 4 v1, Ch 5 v1, and Ch 6 v1 checklist iterations.

---

## Purpose

This file is the single grep target for the rewriter and the verification step. Without this registry, the rules accumulated across eleven amendment rounds risk being applied inconsistently across chapters. Use this file as the authoritative reference for:

- naming canon enforcement (Itqan / BACAB Consulting / GHI / Albassam Group)
- forbidden wordings that must be softened (overclaim language)
- content-placement rules (which content belongs in which chapter)
- structural rules (page allocation, visible sections, boxed elements)
- bibliography rule (no invented citations)
- acceptance rule (no self-approval of compression)

Pairs with `chapter_checklists_v1.md` (which references these rules per-chapter).

---

## Naming-canon rules (apply universally)

| Rule | Forbidden | Required |
|---|---|---|
| **N-1** | "Itqan Tunisie" / any `Itqan + place-name` company form | Itqan = platform name only |
| **N-2** | Hard-coded host company name in chapter prose | Use `\hostCompany` macro; `Commands.tex` resolves to **BACAB Consulting** |
| **N-3** | Hard-coded client name where macro fits | Use `\clientCompany` macro; resolves to **GHI / Albassam Group** (variants "Al Bassam Group", "Gulf Heavy Industries Co.", "GHI" all valid) |
| **N-4** | Mandatory underscore service names in every sentence | Recommended-not-mandatory; underscore form (e.g., `rfq_manager_ms`) appears at least once per service per chapter, typically in subsection headers or tables; prose form ("the manager service") acceptable in flow |

---

## Wording-softening rules (apply wherever the forbidden form appears)

| Rule | Forbidden wording | Required wording | Source |
|---|---|---|---|
| **W-1** | "**status history entry written**" | "**lifecycle timestamps and persisted stage state updated**" | Ch 4 amendment 1; Ch 5 P7.4 |
| **W-2** | "**CI-enforced**" applied to copilot / intelligence / frontend | "**test-enforced through anti-drift tests**" or "**protected by anti-drift tests**" — Manager IS CI-enforced (manager CI workflow exists); copilot is anti-drift-test-enforced | Ch 4 amendment 2; Ch 5 P7.3 |
| **W-3** | "**strict guarantees about the evidence**" / "**strict guarantees**" applied to copilot evidence boundary | "**enforced evidence boundaries and test-backed trust-boundary controls**" or equivalent | Ch 1 reconciliation amendment 2; Ch 4 O7.3 |
| **W-4** | "**working and episodic memory policy**" / "**long-term episodic memory**" framed as imminent | "**memory policy, including current bounded working-memory capture and future episodic-memory extension**" | Ch 4 amendment 4; Ch 5 P7.5 |
| **W-5** | "**synchronous trigger in the present implementation**" (manager → intelligence) | "**manual/direct trigger flows exist; autonomous event-driven manager-to-intelligence flow is deferred**" | Ch 4 amendment 5; Ch 5 P7.7 |
| **W-6** | "**guarantees**" referring to anti-drift tests | "**architectural invariants protected by anti-drift tests**" or "**architectural constraints protected by anti-drift tests**" | Ch 5 amendment 1; Ch 6 Q4.3 |
| **W-7** | "**fully production-ready**" / "**fully integrated**" / "**ensures**" applied to in-scope capabilities | Use scope-honest equivalents per the seven status labels in `scope_discipline_rules.md` | Ch 1 M5; Ch 3 N5; Ch 4 O5; Ch 5 P5; Ch 6 Q5 |
| **W-8** | "**rfq_ui_ms = demonstration-only**" / similar UI dismissal | "**rfq_ui_ms = implemented interface layer with live API support and demo/mock fallback; browser E2E validation pending**" | Ch 4 amendment 3; Ch 5 P7.6 |

---

## Content-placement rules (apply per chapter; forbid leakage)

| Rule | Content type | Permitted location | Forbidden location |
|---|---|---|---|
| **P-1** | Validation numbers (latest verified results — e.g., 259 / 636 / 118 / 11-of-12 / 216 / 98 / 18 / 304 / 64 / 48 / 6 as the audit-snapshot baseline) | **Ch 6 only.** The rewriter must re-run pytest before final submission and update Ch 6 T6.1, T6.3, the prose, and the chapter conclusion if numbers have drifted. | Ch 1, Ch 3, Ch 4, Ch 5 |
| **P-2** | Specific test file names (e.g., `test_no_turn_execution_plan_outside_factory.py`) | Ch 6 §6.4 in light-appendix form; category-level naming in §6.4 main body | Ch 1, Ch 3, Ch 4, Ch 5 |
| **P-3** | Specific code listings beyond the 2 architecture-in-code excerpts (`advance_stage`, `ExecutionPlanFactory`) | Ch 5 only, kept SHORT per Ch 5 amendment 3 | Anywhere else; long full-class dumps forbidden everywhere |
| **P-4** | Pillar-to-pain-point mapping (Pillar 1 ↔ PP-01/05/06/08 etc.) | **Ch 1 only** | Do not duplicate in Ch 3 (per Ch 3 amendment 6) or anywhere else; the traceability matrix composes with the mapping indirectly |
| **P-5** | Boxed design-philosophy quote ("ChatGPT in fluidity, not in authority") | Ch 4 §4.4 only, as visually boxed `\fbox{\parbox{...}}` element | Do not duplicate in Ch 5 / Ch 6 |
| **P-6** | The 8 trust-boundary table | Ch 4 §4.4 (T4.2) | Ch 6 may reference but not reproduce |
| **P-7** | The 18 anti-drift category enumeration | Ch 6 §6.4 (the visible standalone section) | Ch 4 / Ch 5 may reference the count but not enumerate |
| **P-8** | "Status history entry" / "audit-history table" claims | Forbidden everywhere (per W-1); the dormant `rfq_history` model is documented-only and Ch 6 §6.2 / §6.8 explicitly notes the audit-history surface is not implemented | Ch 1, Ch 3, Ch 4, Ch 5, Ch 6 prose |

---

## Structural / format rules

| Rule | Description | Source |
|---|---|---|
| **S-1** | Trust-boundary verification (anti-drift) is a **visible standalone section** in Ch 6 (§6.4), not folded into integration validation | Ch 1 reconciliation amendment 3 |
| **S-2** | Ch 4 §4.4 (copilot trust-boundary architecture) must occupy ~6–7 pp of the 13–15 chapter pages; below 6 pp fails immediately | Ch 4 amendment 7 (Pass 3a gate) |
| **S-3** | Ch 5 §5.3 (copilot implementation) must remain the largest or second-largest section of Ch 5; practical test: a Ch 4-reader can verify implementation matches architecture | Ch 5 amendment 4 |
| **S-4** | Ch 6 should normally target 10–12 pages, but final acceptance depends on evidence completeness and clarity, not page count alone. §6.7 + §6.8 + §6.9 together must occupy at least 3 pp; §6.4 must occupy at least 1 pp | Ch 6 Q10 Pass 7 (with Ch 6 refinement 1) |
| **S-5** | All four light appendices (A: MR-package + workbook reference · B: abbreviated full backlog · C: extended ADR rationale · D: anti-drift test catalogue) total ~4–6 pp, not unlimited | Ch 1 reconciliation amendment 2 |
| **S-6** | The boxed design-philosophy quote in Ch 4 §4.4 must render as a visually boxed element (`\fbox{\parbox{...}{...}}` or equivalent), not merely as italicized prose | Ch 4 amendment 8 |
| **S-7** | Listings stay short (architecture-in-code excerpts only; no long full-function or full-class dumps); pytest invocation listings stay in their 4-line summary form | Ch 5 amendment 3 |
| **S-8** | The use-case diagram (Fig 3.1 v1) shows all 6 target actors with visual marking distinguishing implemented/current flows from target/future flows where the distinction is non-obvious (Administrator, Executive partial) | Ch 1 reconciliation Q4 default; Ch 3 N2.4 |

---

## Bibliography / citation rule

| Rule | Description | Source |
|---|---|---|
| **B-1** | No invented citations. All `\cite{}` must resolve to a real bibliography entry. Drafting uses placeholder keys (`\cite{TODO_*}`); a citation pass resolves them before any chapter is treated as submission-ready | Ch 1 reconciliation amendment 5; Ch 4 / Ch 5 SoA citation pass scheduling |

---

## Acceptance / approval rule

| Rule | Description | Source |
|---|---|---|
| **A-1** | The rewriter does NOT self-approve compression. Each compressed chapter draft must be presented with: (a) a compression diff vs v0, (b) the chapter's must-not-be-lost checklist with verification status per item. The user accepts; the rewriter does not | Ch 1 reconciliation Rule 1 |

---

## Usage notes

- This registry is the single grep target for verifying that no forbidden wording slipped through during chapter rewriting.
- The Ch 6 v1 checklist (in `chapter_checklists_v1.md`) Pass 5 explicitly grep-checks W-2, W-3, W-4, W-5, W-6, P-1, P-8 — that pass uses this registry as its rule source.
- Each chapter's verification procedure (in `chapter_checklists_v1.md`) cross-references rules by their identifier (e.g., "per W-2"), so any rule update propagates automatically through the chapter checklists.
- New rules added in subsequent amendment rounds should be appended here with the next available identifier in the relevant category, with the amendment source noted.
