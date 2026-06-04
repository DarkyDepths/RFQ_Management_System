# Chapter Must-Not-Be-Lost Checklists v1

**Status:** Authoritative consolidation of the six chapter must-not-be-lost checklists accumulated across the eleven amendment rounds of the v0 → v1 transformation work. Each checklist is the FINAL form (after all approved amendments).
**Created:** 2026-05-10
**Owner:** Mohamed Guidara (project author); checklists accumulated in collaboration with Claude Code through the per-chapter iteration rounds.

---

## Purpose

This file is the per-chapter verification gate for the v1 transformation. Each chapter checklist is self-contained: subsection structure, load-bearing claims, required identifiers, required tables/figures, safe-wording phrases, scope-honesty statements, what may be compressed, what must NOT move to appendix, verification procedure.

Per Rule A-1 of `cross_chapter_wording_rules_v1.md`: the rewriter does not self-approve compression. Each compressed chapter draft is presented to the user with the corresponding checklist's verification status filled in. The user accepts.

Pairs with:
- `cross_chapter_wording_rules_v1.md` (the rule source referenced as W-x / N-x / P-x / S-x throughout)
- `citation_map_v1.md` and `bibliography_entries_v1.md` (verified citations available for use in any chapter)
- `scope_discipline_rules.md` (the seven status labels)

---

# Chapter 1 — General Context and Business Problem (reconciled merged checklist)

**Chapter target in v1:** 7–8 pages (compressed from ~18 pp in v0).
**Subsections:** 1.1 Host Organisation and Industrial Context · 1.2 The Estimation Workflow at GHI · 1.3 Documented Pain Points · 1.4 Audit Findings and Why BOQ Automation Was Rejected · 1.5 The Strategic Pivot to RFQ Lifecycle Intelligence · 1.6 Project Identity and Four-Pillar Vision.

**This checklist is a floor, not a ceiling. Style is reviewed separately.**

## M1. Load-Bearing Narrative Arc (six ordered beats)

| # | Beat | Verification |
|---|---|---|
| M1.1 | The audit was conducted in collaboration with **BACAB Consulting** at **GHI / Albassam Group**, examining the RFQ estimation process for pressure vessels and heat exchangers | Grep for "audit" and "BACAB Consulting" in §1.1 or §1.2 — both must appear |
| M1.2 | The original project mandate was **BOQ (Bill of Quantities) automation** | Phrase "BOQ automation" (or close equivalent) must be grep-findable in §1.4 or §1.5 |
| M1.3 | The audit findings demonstrated BOQ automation was the **wrong target** | §1.4 must contain an *argumentative* passage (the three-observation argument, item M4.2) — a one-sentence assertion is insufficient |
| M1.4 | A strategic **pivot / reframing** was made from BOQ automation to RFQ lifecycle intelligence | Word "pivot" or "reframing" must appear in §1.5. The pivot must be presented as deliberate and justified, not as scope drift |
| M1.5 | The **four-pillar vision** emerged from this pivot. All four pillars named: Workflow & Tracking · Communication Automation · Executive Intelligence & BI · Historical Learning & Prediction | All four pillar names present in §1.6 prose, even if Fig 1.3 is omitted |
| M1.6 | Present-work scope: Pillar 1 lifecycle orchestration foundation strongly delivered; Pillar 2 partially addressed; Pillars 3 and 4 mainly future/foundation-scope | Scope status explicit in §1.6 (see M5) |

## M2. Required Identifiers

- **Pain points PP-01 → PP-12** (all 12, with five-family classification: coordination · visibility · historical learning · feasibility risk · tooling fragility)
- **Pillar-to-pain-point mapping** (per P-4 — Ch 1 only, not duplicated elsewhere):
  - Pillar 1 ↔ PP-01/05/06/08 (contributes PP-07)
  - Pillar 2 ↔ PP-02
  - Pillar 3 ↔ PP-03/11
  - Pillar 4 ↔ PP-04/09/10/12 (reinforces PP-07)
- **Four pillars** named in text (Fig 1.3 optional)
- **Entity names** per N-1, N-2, N-3: Itqan (platform) · BACAB Consulting (host firm) · GHI / Albassam Group (client). **"Itqan Tunisie" forbidden.**
- **Service names** spelled exactly as in code at least once (per N-4): `rfq_manager_ms`, `rfq_copilot_ms`, `rfq_intelligence_ms`
- **Reference artifacts**: `SA-AYPP-6-MR-022` may be named briefly once in Ch 1 if useful; **`IF-25144` must NOT appear in Ch 1**
- **LaTeX label keys** must remain stable: `fig:rfq_process`, `fig:rfq_pain_points`, `fig:itqan_pillars`, `tab:pain_points`

## M3. Required Tables and Figures

| Item | Status | Notes |
|---|---|---|
| **Table 1.1 — twelve documented pain points** | Must remain in main body | Cross-referenced from Ch 6 §6.7. Cannot move to appendix |
| **Fig 1.1 — RFQ process flow with overlaid pain points** (merges v0 F1.1 + F1.2) | Must remain in main body | One of seven Tier-1 must-have figures |
| **Fig 1.3 — Four-pillar architecture diagram** | **Optional** | The four-pillar *vision* (text) is mandatory. If Fig 1.3 is omitted, the architecture chapter (Ch 4 v1) must include the stronger architecture visual (per amendment 1) |

## M4. Specific Phrasings That Must Survive

- **M4.1 — Asymmetric cost of error argument** (substance): in industrial estimation, a wrong number propagated into a contractual quotation has a much higher cost than a missing number that prompts a manual review. Justifies the deterministic-first / scope-honest discipline of the entire platform. Verify: grep §1.4 or §1.5 for "asymmetric cost" / "cost of error" / equivalent.
- **M4.2 — Three-observation argument against BOQ automation** (substance): (1) Workbook expertise is uncodified; (2) Historical workbooks lack structured metadata, outcome labels, contextual notes — not training-suitable; (3) Asymmetric cost of error for multi-million-SAR commitments leaves no acceptable failure mode.
- **M4.3 — The reframing paragraph** (substance): §1.5 must contain a paragraph that **explicitly performs** the reframing from "automate the BOQ" to "build the platform inside which BOQ work happens better" / "surround the workbook rather than replace it" — not merely state that a reframing occurred.
- **M4.4 — Project identity statement** (substance): §1.6 must define Itqan as an **"RFQ Lifecycle Intelligence Platform"** with a **"trust-bound conversational copilot"**. Recommended: explicit "what it is not" disclaimers — not a chatbot, not an ERP replacement, not a BOQ automator.
- **M4.5 — Copilot scope-bounding sentence**: "The copilot does not own any pillar of its own; it navigates and explains the data that the pillars produce." Must remain.
- **M4.6 — Working-name qualifier on Itqan**: "Itqan" qualified as a **working name** somewhere in §1.6.

## M5. Scope-Honesty Statements Required in §1.6

| # | Statement | Why |
|---|---|---|
| M5.1 | Pillar 1 lifecycle orchestration foundation is strongly delivered (via `rfq_manager_ms`) | Defines the strongest delivered scope |
| M5.2 | Pillar 2 must remain framed as partial/foundation-level (reminders, communication support, workflow visibility); Pillar 3 remains mainly future/foundation-level. Endpoint-level audit detail belongs to Ch 5/Ch 6 | Honest framing without leaking implementation detail |
| M5.3 | Pillars 3 and 4 are mainly future-scope or foundation-scope; Pillar 4 is a **foundation** of document parsing capabilities, predictive components left as **future work**. The words "foundation" and "future work" are load-bearing | Prevents overclaim about predictive intelligence |
| M5.4 | The platform is a **foundation; full vision realisation is multi-year** | Frames work honestly |
| M5.5 | The **trust-bound conversational copilot is the principal innovation contribution** of the present work, characterised by **enforced evidence boundaries and test-backed trust-boundary controls** (per W-3, NOT "strict guarantees") | Anchors the innovation claim |

**Forbidden in Ch 1:** validation numbers (per P-1 — Ch 6 only); implementation specifics (anti-drift count, Path numbering, FakeLlmConnector, capture-only memory — Ch 4/5/6 only); "strict guarantees" (per W-3); compound names like "Itqan Tunisie" (per N-1).

## M6. Naming-Canon Enforcement (per registry)

Per N-1 to N-4. Confirm `\hostCompany` resolves to BACAB Consulting; `\clientCompany` resolves to GHI / Albassam Group. No "Itqan Tunisie".

## M7. v0 Errata to Fix During the Rewrite

- **M7.1** Line 115 of v0 Ch 1 contains a duplicated sentence: *"The standards are well known, and the staff are competent."* appears twice consecutively. Delete the duplicate.
- **M7.2** Confirm `\hostCompany` and `\clientCompany` macros in `Commands.tex` resolve to canonical names.

## M8. What May Be Compressed or Moved to Light Appendix

- MR-022 sixteen-section enumeration → ~70% cut; light appendix (factual reference)
- 36-sheet workbook detailed breakdown → ~70% cut; light appendix
- Audit methodology prose → ~60% cut; 1–2 paragraphs in §1.4
- Pain-point family commentary → light cut; **stays in main body**
- Repeated pivot framing → cut redundancy; pivot in §1.5 only, no echo in §1.6
- §1.7 Methodology Overview teaser (v0) → **delete** (lives in Ch 3 v1)
- "From Symptoms to Diagnosis" filler paragraph → **delete**
- Final transitional paragraph of §1.5 → **delete**

## M9. Content That Must NOT Move to Appendix

- Twelve pain points (Table 1.1)
- Four-pillar named enumeration with scope status
- Audit → BOQ rejection → pivot narrative
- Asymmetric cost of error argument
- Project identity statement
- Pain-point family commentary

## M10. Verification Procedure

**Pass 1 — Structural check.** Six narrative beats (M1.1 → M1.6) in order. All 12 pain points in Table 1.1. All four pillars named. Naming canon (no "Itqan Tunisie"). v0 errata M7.1 fixed.
**Pass 2 — Argumentative check.** §1.4 + §1.5 read as connected argument. BOQ rejection (M4.2) and pivot (M4.3) **performed**, not asserted. Asymmetric cost of error (M4.1) appears.
**Pass 3 — Scope-honesty check.** All five scope statements (M5.1 → M5.5) in §1.6. Future-scope/foundation framing for Pillars 3/4. **"Enforced evidence boundaries"** wording for copilot, not "strict guarantees" (per W-3). No validation numbers (per P-1).
**Pass 4 — Cross-reference check.** Table 1.1 and Fig 1.1 present (Fig 1.3 optional). PP-01 → PP-12 unchanged from v0. Pillar-to-pain-point mapping (M2) preserved. LaTeX label keys unchanged. `IF-25144` does NOT appear.

---

# Chapter 2 v1 — State of the Art and Technological Background (creation checklist)

**Chapter target in v1:** 8–9 pages (NEW chapter, no v0 source).
**Subsections:** 2.1 Introduction · 2.2 Industrial Quotation and RFQ Management Systems · 2.3 Microservices and Layered Architecture Patterns · 2.4 LLM-Powered Conversational Systems: A Taxonomy · 2.5 Grounding, Hallucination, and AI Safety Concerns · 2.6 Document Intelligence in Engineering Contexts · 2.7 Comparative Analysis and Positioning.

## R1. Chapter Mission and Discipline

**R1.1 — Five questions Ch 2 must answer:**
1. What technologies and concepts does the project rely on?
2. What existing solutions or approaches already exist?
3. Why are they not sufficient for the specific GHI RFQ lifecycle problem?
4. Why is the proposed platform technically justified?
5. Why is the trust-bound copilot architecture relevant and innovative?

**R1.2 — Forward-pointer per subsection:** Each §2.x subsection must clearly justify **at least one** later architectural, methodological, or implementation decision (per amendment 4 — relaxed from "every paragraph" to "per subsection").

**R1.3 — Cautious wording:** "addresses a gap" / "is positioned as" / "combines" / "supports". Avoid: "first / only / best / outperforms / revolutionary / unique".

## R2. Section-by-Section Scope (use citation_map_v1.md for citation placement)

**§2.1 Introduction (~0.5 pp)** — Three SoA dimensions: industrial RFQ/quotation systems · microservices/layered patterns · LLM conversational systems with grounding/safety. No citations.

**§2.2 Industrial Quotation and RFQ Management Systems (~1 pp)** — ERP-embedded quoting (cite `sap_cpq_product` as category exemplar only, per amendment 4); CPQ tools (cite `salesforce_cpq_docs` as category exemplar); bespoke Excel workflows (link to Ch 1); workflow/BPM systems (cite `dumas2018bpm`). Removed-slot framings: 2.2.C analyst report removed; 2.2.D RFQ workflow academic softened to "as observed at GHI during the audit (Ch 1)" + `dumas2018bpm`. **Forward pointer:** Ch 4 §4.3 manager service.

**§2.3 Microservices and Layered Architecture Patterns (~1 pp)** — Microservices (cite `newman2021microservices`); Hexagonal Architecture (cite `cockburn2005hexagonal`); Clean Architecture (cite `martin2017cleanarch`); Domain-Driven Design (cite `evans2003ddd` per approved decision — frame Evans as the domain-modelling tradition behind the manager service's seven-entity domain model). BACAB attributed to `\hostCompany`, NOT cited as academic pattern. **Forward pointer:** Ch 4 §4.2 BACAB pattern + service decomposition.

**§2.4 LLM-Powered Conversational Systems (~2 pp — academic core)** — Foundational LLM (cite `brown2020gpt3`); Family 1 Naive RAG (cite `lewis2020rag`); Family 2 LLM agents (cite `yao2023react`); Family 3 Constrained tool-calling (cite `anthropic_tool_use_docs`); Family 4 Trust-bounded systems (no forced citation per amendment 5; framed as project's positioning). Removed-slot framing: 2.4.E meta-survey removed; use "this chapter cites the seminal contribution to each family rather than a meta-survey". **Forward pointer:** Ch 4 §4.4 trust-boundary architecture + alternative-architectures positioning. **Visual:** Fig 2.1 Conversational AI taxonomy.

**§2.5 Grounding, Hallucination, and AI Safety (~1.5 pp)** — Hallucination survey (cite `ji2023hallucination`); Constitutional AI / policy-as-data (cite `bai2022constitutional`); LLM-as-Judge (cite `zheng2023judge`); structured outputs (cite `anthropic_structured_outputs_docs`). **Forward pointer:** Ch 4 §4.4 + Ch 5 §5.3 dual layer + Ch 6 §6.4 anti-drift validation.

**§2.6 Document Intelligence (~1 pp)** — ASME (cite `asme_bpvc_viii_div1_2025`) + TEMA (cite `tema_standards_11ed`); deterministic Excel/PDF parsing vs LLM doc QA. Softened-slot framing: 2.6.C document intelligence survey softened to "the asymmetric cost of error from Ch 1 §1.5 and demonstrated by the parser implementations in Ch 5 §5.4". **Forward pointer:** Ch 4 §4.2 + Ch 5 §5.4 intelligence service.

**§2.7 Comparative Analysis and Positioning (~1.5 pp + Table 2.1)** — Synthesis matrix: 7 rows (ERP-embedded · CPQ · Bespoke Excel · Naive RAG · LLM agent · Constrained chatbot · Itqan) × 6 columns (lifecycle awareness · multi-actor coordination · evidence grounding · scope-bounded refusal · policy-as-configuration · cost-of-error posture). **Forward pointer:** Ch 4 + Ch 5 + Ch 6 (whole rest of report defends the cell).

## R3. Concepts That MUST Be Covered

13 concepts (C1–C13) covering: ERP/CPQ/Excel categories · microservices · Hexagonal/Clean lineage · 4 LLM conversational families · hallucination · LLM-as-Judge · deterministic doc parsing · asymmetric cost of error.

## R4. Anti-Patterns to Avoid

Don't explain transformers. Don't generic "rise of AI" preamble. Don't list every CPQ product. Don't claim "first/only/best". Don't cite without verification (per B-1). Don't redo Ch 4 §4.4 in literature-review form. Don't restate Ch 1 audit findings. Don't cite BACAB academically. Don't copy from reference reports.

## R5. Forward-Pointer Mapping (R1.2 enforcement)

| Subsection | Justifies | Located in |
|---|---|---|
| §2.2 | Manager service as distinct lifecycle-orchestration layer | Ch 4 §4.3 |
| §2.3 | BACAB layered pattern + 6-service decomposition | Ch 4 §4.2 |
| §2.4 | Trust-boundary architecture vs three alternatives | Ch 4 §4.4 |
| §2.5 | Dual layer (deterministic guardrails + LLM Judge) | Ch 4 §4.4 + Ch 5 §5.3 + Ch 6 §6.4 |
| §2.6 | Intelligence service deterministic-parsing-first; FR-INT-04 | Ch 3 §3.2 + Ch 4 §4.2 + Ch 5 §5.4 |
| §2.7 | Whole rest of report defends Itqan's matrix cell | Ch 4 + Ch 5 + Ch 6 |

## R6. Citation Discipline (per B-1)

17 verified citations from `citation_map_v1.md` and `bibliography_entries_v1.md`. No `\cite{TODO_*}` may remain in final draft. No invented citations. Use placeholder keys during drafting if needed; resolve before submission.

## R7. Tables and Figures

**Tier 1 (must-have):**
- **NEW Table 2.1** — Comparative positioning matrix (7 rows × 6 columns) — `tabularx` + `booktabs`
- **NEW Fig 2.1** — Conversational AI architecture taxonomy (4 families) — Excalidraw / draw.io

**Tier 2 (nice-to-have):**
- **NEW Fig 2.2** — Hallucination defense layering — promote to Tier 1 only if §2.5 has page room

## R8. Verification Procedure

**Pass 1 — Mission-and-discipline check.** Five questions (R1.1) addressed across §2.1–§2.7. Each subsection §2.2–§2.6 has at least one forward pointer (R1.2 + R5). Cautious wording grep returns zero matches for "first / only / best / revolutionary / outperforms".
**Pass 2 — Concept-coverage check.** All 13 must-cover concepts (C1–C13) appear in their assigned subsection. Four conversational-AI families named in §2.4. BACAB attributed to `\hostCompany` per N-2.
**Pass 3 — Anti-generic-theory check.** Grep for transformer / attention / "rise of AI" / "outperforms" / "first-of-its-kind" — zero matches.
**Pass 4 — Citation-discipline check (per B-1).** Grep `\cite{TODO_*}` — zero matches in submission-ready state. Every `\cite{X}` resolves to a verified `\bibitem{X}`.
**Pass 5 — Visual completeness check.** Table 2.1 present (7 rows × 6 cols). Fig 2.1 present and not placeholder. Fig 2.2 present if pages permitted.
**Pass 6 — Naming-canon and cross-chapter wording check (per registry).** Grep for "Itqan Tunisie" (zero), "strict guarantees" (zero), and other forbidden wordings from W-1 to W-8. Macros `\hostCompany`/`\clientCompany` consistent.

---

# Chapter 3 v1 — Requirements, Methodology, and Project Management

**Chapter target in v1:** 8–9 pages (compressed from ~25 pp v0 Ch 2).
**Subsections:** 3.1 Stakeholders and Actors · 3.2 Functional Requirements · 3.3 Non-Functional Requirements · 3.4 Use Cases and Activity Diagrams · 3.5 Methodology (Scrumban, Documented Terminal State, ADR Discipline) · 3.6 Risk Management and Traceability Matrix.

## N1. Load-Bearing Narrative Arc (six ordered beats)

| # | Beat |
|---|---|
| N1.1 | Stakeholders (4) and actors (6) distinguished — stakeholders shape success criteria, actors interact with platform |
| N1.2 | FR derived from Ch 1 audit findings — pain point → requirement chain |
| N1.3 | NFR includes standard concerns (REL, SEC, MNT, OPS) AND AI Integrity (distinctive) |
| N1.4 | Use cases + activity diagrams expose lifecycle stage advancement (manager) and copilot turn (trust-bound pipeline) |
| N1.5 | Scrumban + Documented terminal state + ADR register + risk register together form project-management discipline |
| N1.6 | Traceability matrix bridges Ch 1 pain points → Ch 6 business impact via FR identifiers |

## N2. Required Identifiers

**N2.1 — All 25 FR identifiers (must survive verbatim, statements may be shortened per amendment 3):**
- Manager: FR-MGR-01 → 08 (8 IDs)
- Copilot: FR-COP-01 → 08 (8 IDs)
- Intelligence: FR-INT-01 → 04 (4 IDs)
- UI: FR-UI-01 → 03 (3 IDs)
- Cross-cutting: FR-X-01, 02 (2 IDs)
- **Total: 25 FR identifiers**

**N2.2 — All 19 NFR identifiers (must survive verbatim, statements may be shortened):**
- Reliability (REL): NFR-REL-01 → 04 (4)
- Security (SEC): NFR-SEC-01 → 04 (4); NFR-SEC-01 + NFR-SEC-04 keep "deferred to future scope" wording for IAM
- AI Integrity (AI): NFR-AI-01 → 04 (4); NFR-AI-04 is trust-boundary anchor
- Maintainability (MNT): NFR-MNT-01 → 03 (3); NFR-MNT-02 keeps BACAB reference; NFR-MNT-03 keeps ADR register reference
- Operability (OPS): NFR-OPS-01 → 04 (4)
- **Total: 19 NFR identifiers**

**N2.3 — 4 stakeholders:** academic supervisor (ENET'COM) · professional supervisor (`\hostCompany`) · technical/leadership at `\clientCompany` · academic jury.

**N2.4 — 6 system actors (per S-8):** Estimation Manager · Estimator · Department User · Executive · Administrator · Copilot User. Use case diagram shows all 6 with visual marking distinguishing implemented/current vs target/future flows.

**N2.5 — Backlog identifiers (per amendment 1):** Per amendment 1 — main chapter preserves backlog families, priority logic, representative IDs. Full 19-ID list (B-MGR-01 → B-X-03) may move to light appendix. **B-X-03 must remain visible in main chapter** (anchors deferred IAM scope).

**N2.6 — Other named artefacts:** ADR register (6-part structure: context · options · decision · justification · consequences · validation); Risk register (4-part structure: description · impact · mitigation · review notes); Control Center (per amendment 5 — brief mention only, not load-bearing).

**N2.7 — LaTeX label keys:** `tab:stakeholders`, `tab:fr_*`, `tab:nfr`, `tab:backlog_*`, `tab:traceability`, `fig:use_cases`, `fig:activity_advance_stage`, `fig:activity_ask_copilot`, `fig:sprint_timeline`.

## N3. Required Tables and Figures

| Item | Status | Notes |
|---|---|---|
| Stakeholder alignment matrix (T2.1 v0 / T3.1 v1) | Must remain | Cadence/Approach/Proof columns survive |
| FR tables (Manager, Copilot, Intelligence, UI/Cross-cutting) | Must remain | Identifier columns non-negotiable; statements may be shortened per amendment 3 |
| NFR table | Must remain | Single grouped table; all 19 rows; NFR-SEC + NFR-REL caveats survive |
| Consolidated backlog synopsis | Must remain | Single priority-tagged table; full backlog → light appendix per amendment 1 |
| Fig 3.1 v1 — Use case diagram | Must remain | All 6 actors per N2.4 |
| Fig 3.2 v1 — Activity: Advance RFQ Stage | Must remain (per amendment 2) | Three-gate logic visible |
| Fig 3.3 v1 — Activity: Ask Copilot About RFQ | Recommended (per amendment 2) | If page pressure severe, may be replaced by Ch 4/5 turn pipeline diagram; the copilot flow concept must not disappear |
| Sprint timeline (Fig 2.4 v0) | Optional / appendix | Not central |
| Traceability matrix (per amendment 4) | Must remain in main body | Compactable: shorter validation refs (e.g., "Ch 6 §6.3"-style), `\footnotesize`, landscape orientation if needed |

## N4. Specific Phrasings That Must Survive

- **N4.1 — FR-INT scope-honesty preface**: "current-scope foundation requirements" + "deliberately excluded from these requirements and remain future scope"
- **N4.2 — FR-MGR-07 hardening caveat**: "comprehensive audit-log expansion is treated as a hardening concern beyond the current scope" (per W-1 / P-8)
- **N4.3 — FR-COP-04 evidence-source caveat**: "primarily manager service state in the implemented operational paths, with intelligence service artifacts incorporated as those paths become available"
- **N4.4 — NFR-AI-04 trust-boundary anchor (per amendment 8)**: Verify v0 wording does not contain overclaim language ("guarantee", "ensure", "fully"). If it does, soften per W-3. Anchor status preserved through content, not specific overclaim wording.
- **N4.5 — NFR-SEC-01 + NFR-SEC-04 deferred-IAM caveats**: explicit "full integration with a dedicated identity service is deferred"
- **N4.6 — Documented Terminal State**: 6-state Scrumban board ending in "Documented" as separate terminal state with WIP limit
- **N4.7 — Activity-diagram bounded-LLM-stages framing**: "the language model is invoked at specific, bounded stages of the flow"
- **N4.8 — Three-purpose framing of traceability matrix**: reader navigation · structural quality check · Ch 6 business-impact composition

## N5. Scope-Honesty Statements

| # | Statement |
|---|---|
| N5.1 | FR-INT requirements are foundation/parsing only; predictive scope is future work |
| N5.2 | Full IAM deferred; current scope = actor-context headers + manager-mediated retrieval + minimal auth shim |
| N5.3 | Comprehensive audit-log surface is hardening concern; current traceability via timestamps + status history (per W-1) |
| N5.4 | Copilot authority bounded to deterministic platform components, not LLM (NFR-AI-04) |
| N5.5 | Backlog priorities reflect demonstration-readiness, not long-term importance; B-X-03 deliberately deferred |

**Forbidden in Ch 3:** validation numbers (per P-1, Ch 6 only); per amendment 7, **no validation evidence pre-cite** in chapter conclusion (acceptable to bridge to Ch 6 with phrases like "the requirements catalogue is the contract that Chapter 6 will exercise" but no specific numbers/classes).

## N6. Naming-Canon Enforcement

Per N-1 to N-4. Service names recommended-not-mandatory in every sentence per N-4.

## N7. v0 Errata to Fix

- **N7.1 — Cross-chapter renumbering:** "Chapter 3" → Chapter 4, "Chapter 4" → Chapter 5, "Chapter 5" → Chapter 6 throughout v0 Ch 2
- **N7.2 — Traceability matrix Validation column:** "Ch. 5 (…)" → "Ch. 6 (…)" in all rows
- **N7.3 — `\hostCompany` / `\clientCompany` macro resolution check**

## N8. What May Be Compressed or Moved to Light Appendix

- Stakeholder prose intro → ~30%
- FR table prose intros → 1 sentence each (~60%)
- NFR intro paragraph → ~50%
- **Product Backlog: 3 tables → 1 consolidated synopsis** (~75% cut, biggest single compression)
- Activity diagram explanatory paragraphs → ~40%
- Scrumban prose → 1 paragraph (~50%)
- ADR practice prose → ~50% (6-part structure remains enumerated)
- Risk Management → 4–5 lines (~60%); 4-part structure remains enumerated
- Control Center → 1 sentence (per amendment 5)
- Sprint timeline → optional / appendix
- Full backlog (B-MGR-01 → B-X-03) → light appendix per amendment 1; B-X-03 visible in main

## N9. Content That Must NOT Move to Appendix

- Stakeholder alignment matrix
- All 25 FR identifiers + all 19 NFR identifiers (statements may shorten)
- Consolidated backlog synopsis with all 19 IDs visible (per amendment 1; B-X-03 must remain visible)
- Use-case diagram (all 6 actors)
- Both activity diagrams (Advance Stage required; Ask Copilot recommended)
- Traceability matrix (per amendment 4 — compactable but in main)
- Scrumban + Documented terminal state framing
- ADR practice description with 6-part structure
- Risk register practice description with 4-part structure
- All five scope-honesty statements (N5.1 → N5.5)

## N10. Verification Procedure

**Pass 1 — Identifier preservation.** Grep for all 25 FR + 19 NFR identifiers. 4 stakeholders + 6 actors named. All 19 backlog IDs in synopsis (or representatives + B-X-03 per amendment 1).
**Pass 2 — Cross-reference renumbering (N7.1).** Grep "Chapter 3/4/5"; remap correctly. Traceability matrix Validation column → "Ch. 6".
**Pass 3 — Scope-honesty check.** Five scope statements (N5.1 → N5.5) appear. Four required caveats (N4.1, N4.2, N4.3, N4.5) survive. "Deferred to future scope" wording used. **No validation numbers or specific evidence classes pre-cited (per amendment 7).**
**Pass 4 — Methodology and innovation framing.** 6-state Scrumban with Documented (N4.6). NFR-AI-04 wording verified non-overclaim per amendment 8. Bounded-LLM-stages framing (N4.7). ADR 6-part + Risk 4-part structures enumerated.
**Pass 5 — Traceability and cross-reference.** Matrix present, all 25 FRs, three-purpose framing (N4.8). LaTeX label keys (N2.7) unchanged. Naming canon (N6.1 → N6.5).

---

# Chapter 4 v1 — Conceptual and Technical Architecture

**Chapter target in v1:** 13–15 pages (compressed from ~34 pp v0 Ch 3).
**Subsections:** 4.1 Global Architecture and Four-Pillar Layering · 4.2 Microservices Inventory and BACAB Pattern · 4.3 Manager Service: Domain Model and Lifecycle · 4.4 Copilot Service: Trust-Boundary Architecture (~6–7 pp protected per S-2) · 4.5 Evidence Boundary · 4.6 Platform Integration and ADR Summary.

**This is the most architecturally consequential chapter.** §4.4 must survive 6–7 pp from a v0 source of ~10 pp without losing innovation depth.

## O1. Load-Bearing Narrative Arc (six ordered beats)

| # | Beat |
|---|---|
| O1.1 | Itqan organises into layered architecture (presentation/orchestration/intelligence/data) + microservices set; manager = backbone, copilot = principal innovation |
| O1.2 | Four pillars revisited as architectural map; copilot is NOT a pillar, but a cross-cutting layer |
| O1.3 | Manager service mission deliberately narrowed (lifecycle orchestration only); discipline via three-gate stage progression (mandatory-field, blocker, transition-validity) |
| O1.4 | Copilot innovation: separates fluidity (LLM) from authority (deterministic); positions vs three alternatives; commits to 8 trust boundaries with named owners; single-construction discipline via ExecutionPlanFactory |
| O1.5 | Evidence boundary enforceable (not declarative): policy-as-config (Path Registry) + single-construction (Factory + protected by anti-drift tests) + deterministic guardrails + LLM Judge |
| O1.6 | Architecture composes 4 implemented services into integrated platform via disciplined contracts; ADR table summarises decisions |

## O2. Required Identifiers and Concepts

**O2.1 — Service inventory (6 services, 4 implemented + 2 future):** `rfq_manager_ms` · `rfq_copilot_ms` · `rfq_intelligence_ms` (foundation level) · `rfq_ui_ms` (per W-8 — implemented interface layer with live API support and demo/mock fallback; browser E2E pending) · `rfq_iam_ms` (future) · `rfq_communication_ms` (future).

**O2.2 — BACAB layered pattern (5 active + 3 support):** routes · controllers · datasources · translators · connectors (active); models · config · utils (support). Discipline rules: routes don't contain business logic; controllers don't access DB directly; datasources don't make decisions.

**O2.3 — Manager service 7 entities:** RFQ · Workflow · RFQ_Stage · Subtask · Note · File · Reminder.

**O2.4 — Manager three-gate progression:** mandatory-field gate · blocker gate · transition-validity gate. Atomic-from-caller advance commit (per W-1): current stage marked complete with timestamp · next stage activated · RFQ progress recomputed · **lifecycle timestamps and persisted stage state updated** (NOT "status history entry written").

**O2.5 — Copilot eight trust boundaries (all 8 must survive in T4.2 with owners):**
1. What path? FastIntake OR LLM Planner → PlannerValidator → ExecutionPlanFactory
2. Who constructs plan? ExecutionPlanFactory only (per W-6 — protected by anti-drift tests, NOT "CI-enforced" since copilot has no CI workflow)
3. Which tools? Path Registry + deterministic Tool Executor
4. May user read RFQ? Manager service API (404/403)
5. Which fields enter LLM? Per-path field whitelist in Path Registry
6. Which target does field belong to? Per-target labelling at evidence-packet construction
7. Hallucinate/drift/leak? Deterministic Guardrails + LLM Judge as final defense
8. Failure handling? Escalation Gate → re-enters factory with structured `reason_code`

**O2.6 — Two classification sources + factory + three-type contract:** FastIntake (deterministic, anchored regex) → `IntakeDecision`; LLM Planner → `PlannerProposal` → PlannerValidator (structural only) → `ValidatedPlannerProposal`; ExecutionPlanFactory (single permitted constructor of `TurnExecutionPlan`); Escalation Gate (single deterministic intercept, calls factory through separate entry to construct Path 8 plan).

**O2.7 — Path Registry policy elements:** permitted intake sources · authorized evidence tools · allowed/forbidden fields · target resolver strategy · access policy · active guardrails · Judge policy and triggers · **memory policy, including current bounded working-memory capture and future episodic-memory extension** (per W-4) · persistence policy · finalizer template keys keyed by reason code · model profile. Anti-drift-test-enforced: only Factory + Escalation Gate may read Path Registry.

**O2.8 — Five evidence sources:** conversation · manager service state (dominant in v1) · intelligence service artifacts (NOT wired in current implementation) · controlled domain knowledge (future) · absence of permitted evidence (Path 8).

**O2.9 — Path coverage in present work:** Path 1 (FastIntake/trivial), Path 4 (RFQ-grounded demo-defining), Path 8 family (5 sub-cases). Paths 2/3/5/6/7 short-circuit through Escalation Gate to Path 8.1 — "not degraded behaviour".

**O2.10 — Pipeline stages:** Target resolution → Access (manager-mediated) → Memory Load → Tool Executor → Evidence Check → Context Builder → Compose (with Path 4 deterministic renderer) → Guardrails → Judge → Finalizer → Persist.

**O2.11 — Memory architecture (per W-4):** working memory captured per-turn, persisted; **two extensions explicitly NOT IMPLEMENTED**: (1) injection into Planner/Compose/Judge prompts; (2) future episodic-memory extension across sessions.

**O2.12 — ADR summary (T4.3 — all 8 rows):** Service decomposition (Microservices) · Intra-service pattern (BACAB layered) · Operational source of truth (Manager) · Reminder ownership (Inside manager) · Conversational design (Trust-bound copilot) · Policy surface (Policy-as-config via Path Registry) · Plan construction (Single ExecutionPlanFactory) · IAM (In-service auth now, dedicated IAM deferred).

**O2.13 — LaTeX label keys:** `fig:itqan_global` (F4.1, merges v0 F3.1+F3.2), `fig:manager_erd` (F4.2 per amendment 6 — recommended in main, appendix only if extreme page pressure), `fig:trust_boundary` (F4.3 — flagship redesign per S-6), `fig:evidence_boundary` (F4.4), `tab:pillar_scope` (T4.1), `tab:trust_boundaries` (T4.2), `tab:decisions` (T4.3).

## O3. Required Tables and Figures

| Item | Status | Notes |
|---|---|---|
| T4.1 — Pillar scope status | Must remain | All 4 rows |
| T4.2 — Eight trust boundaries | Must remain | All 8 rows with Owner |
| T4.3 — ADR summary | Must remain | All 8 ADR rows |
| F4.1 — Global architecture (merged F3.1+F3.2) | Must remain | 4 layers + microservices + cross-cutting copilot |
| F4.2 — Manager ERD (per amendment 6) | Recommended in main; appendix only if extreme page pressure | Proves domain modeling maturity |
| **F4.3 — Trust-boundary architecture (FLAGSHIP)** | Must remain | Color-coded by trust class |
| F4.4 — Evidence boundary decision flow | Must remain | Companion to F4.3 |

## O4. Specific Phrasings That Must Survive

- **O4.1 — Boxed design-philosophy quote (verbatim, per S-6):** *"The copilot should feel like ChatGPT in fluidity, but must not behave like generic ChatGPT in authority. Its authority comes from platform evidence, not from the language model."* Renders as `\fbox{\parbox{...}}` element, NOT italicised prose.
- **O4.2 — Fluidity / authority distinction**: must remain in §4.4 explanation.
- **O4.3 — Eight-boundary mantra (verbatim):** *"Two classification sources, one plan factory, one escalation gate; the language model produces language, code produces truth, policy enforces boundaries, the Judge verifies, templates render the safe answer when nothing else worked."*
- **O4.4 — Three reasons for innovation:** structural (type-level + build-level enforcement) · operational (every decision observable/auditable) · academic (defensible answer to: how should LLM-driven systems behave when cost of being wrong is high).
- **O4.5 — Three properties that make evidence boundary enforceable:** policy-as-configuration (Path Registry) · single-construction (Factory + anti-drift tests, per W-6) · deterministic guardrails + LLM Judge (Judge is "last line of defense, not the first").
- **O4.6 — Reminder-ownership ADR rationale:** data ownership boundary defense — extracting reminders would require either caching lifecycle state OR synchronous round trips.
- **O4.7 — "Copilot is not a fifth pillar" framing**: must survive in §4.1.
- **O4.8 — Single-construction discipline framing (per W-2 / W-6):** anti-drift tests in copilot pytest suite, NOT "continuous integration check on every commit to copilot repository" (copilot has no CI workflow).

## O5. Scope-Honesty Statements (per audit-truth)

| # | Statement |
|---|---|
| O5.1 | Pillar 4 is foundation only; predictive layer is future scope |
| O5.2 | `rfq_iam_ms`, `rfq_communication_ms` are future scope; current = minimal in-service shims |
| O5.3 | Intelligence-copilot connector NOT wired; deferred to Path 5 slices |
| O5.4 | Memory: capture-only; injection deferred; future episodic-memory extension (per W-4) |
| O5.5 | Paths 2/3/5/6/7 short-circuit to Path 8.1 |
| O5.6 | Manager → intelligence: manual/direct trigger; autonomous event-driven flow deferred (per W-5) |
| O5.7 | No unified root compose; per-service compose only |

**Forbidden in Ch 4:** validation numbers (per P-1, Ch 6 only); specific test file names (per P-2, Ch 6 only); specific code listings (per P-3, Ch 5 only); concrete file paths under `microservices/` (Ch 5 only); "strict guarantees" (per W-3); "CI-enforced" for copilot (per W-2); compound names (per N-1).

## O6. Naming-Canon Enforcement

Per N-1 to N-4. BACAB attributed to `\hostCompany`. §4.2 line about BACAB-pattern provenance from host-firm conventions must remain.

## O7. v0 Errata to Fix

- **O7.1 — Cross-chapter renumbering:** "Chapter 2" → Chapter 3, "Chapter 4" → Chapter 5, "Chapter 5" → Chapter 6 throughout v0 Ch 3
- **O7.2 — §-references** re-mapped to v1 §4.x
- **O7.3 — Overclaim softening at v0 line 170 (per W-3):** "strict guarantees" → "enforced evidence boundaries and test-backed trust-boundary controls"
- **O7.4 — Endpoint count drift:** "approximately thirty-one" — verify against current code grep before final
- **O7.5 — Macro resolution check**

## O8. What May Be Compressed

- §3.2 introductory paragraphs about layered discipline → ~50%
- §3.2 redundant restatement of pillar definitions from Ch 1 → DELETE
- §3.3 inter-service communication → 1 paragraph (~50%)
- §3.4 manager mission → 1 paragraph (~40%)
- §3.4 reminder ADR → ~40% (data-ownership defense O4.6 verbatim)
- §3.4 API contract overview → ~50%
- §3.5 design philosophy explanations → ~30% (O4.1 boxed, O4.2 distinction survive)
- §3.5 positioning (3 alternatives) → 4–5 lines each (~50%)
- §3.5 Pipeline & Five Evidence Sources → bullet-style (~40%); all 5 sources named
- §3.5 Memory architecture → ~50%; both deferred extensions explicit per W-4
- §3.5 Path coverage → ~30%; Path 1/4/8 vs 2/3/5/6/7 explicit
- §3.6 "Why enforceable" → ~40%; all 3 properties enumerated
- §3.7 Data Model + API Contracts → ~60% → 1–1.5 pp
- §3.7 closing deployment-posture paragraph → DELETE
- §3.8 Platform Integration → ~50%

**Light appendix candidates:** extended ADR rationale for 1–2 high-impact ADRs (Trust-bound copilot + Reminder ADR are top candidates).

## O9. Content That Must NOT Move to Appendix

- Layered architecture (4 layers) + four-pillar architectural map + T4.1
- Service inventory (4+2) + BACAB pattern (5+3 layers) + discipline rules
- Three deterministic gates of manager service
- Boxed design-philosophy quote (per S-6)
- Eight trust boundaries (T4.2) with all 8 owners
- Eight-boundary mantra (O4.3)
- Two classification sources / one factory / three-type contract
- Path Registry policy elements + anti-drift-test-enforced reader allowlist
- Five evidence sources + Path 5 deferral + intelligence-connector-not-wired honesty
- Memory architecture posture + 2 deferred extensions (per W-4)
- Path coverage (Path 1/4/8 vs 2/3/5/6/7)
- Three reasons for innovation (O4.4)
- Three properties making evidence boundary enforceable (O4.5)
- ADR summary table (T4.3) — all 8 rows; IAM ADR row anchors deferred-scope honesty

## O10. Verification Procedure

**Pass 1 — Structural check.** Six narrative beats (O1.1 → O1.6) in order. 6-service inventory, BACAB 5+3, 7 manager entities, 3 gates, 8 trust boundaries with owners, 5 evidence sources all named. Naming canon (no "Itqan Tunisie").
**Pass 2 — Cross-reference renumbering (O7.1, O7.2).**
**Pass 3 — Innovation depth check.** Boxed quote (O4.1) survives **verbatim** as visually boxed `\fbox{\parbox{}}` (per S-6). Eight-boundary mantra (O4.3) verbatim. 3 alternative architectures (naive RAG, LLM agent, uncontrolled tool-calling chatbot) named with 4–5 line treatment each. Three reasons closing argument (O4.4). Three-type contract named.
**Pass 3a — Page allocation enforcement (per S-2).** §4.4 occupies ~6–7 of 13–15 pp. **If §4.4 falls below 6 pp, chapter fails immediately, regardless of other content quality.**
**Pass 4 — Scope-honesty check.** All 7 scope-honesty statements (O5.1 → O5.7). O7.3 overclaim softening applied (grep "strict guarantees" → zero). No validation numbers (per P-1), no specific code listings (per P-3), no specific test names (per P-2). "Deferred / future scope / not wired / captured only" framings used.
**Pass 5 — Evidence-boundary enforceability.** §4.5 enumerates all 3 properties (O4.5). Judge as "last line of defense, not first". Path Registry anti-drift-test-enforced reader allowlist stated (per W-2).
**Pass 6 — Cross-reference and visual completeness.** T4.1, T4.2, T4.3 present (4/8/8 rows). F4.1 (global), F4.3 (trust-boundary, redesign per S-6), F4.4 (evidence boundary) present and not placeholders. F4.2 (manager ERD) recommended in main per amendment 6. LaTeX label keys (O2.13) unchanged. Conclusion forward-points to Ch 5 + Ch 6.

---

# Chapter 5 v1 — Implementation

**Chapter target in v1:** 9–11 pages (compressed from ~27 pp v0 Ch 4).
**Subsections:** 5.1 Development Environment and Toolchain · 5.2 Manager Service Implementation · 5.3 Copilot Service Implementation (largest or 2nd-largest section per S-3) · 5.4 Intelligence Service Implementation · 5.5 UI Implementation · 5.6 Cross-Service Integration Status.

## P1. Load-Bearing Narrative Arc (six ordered beats)

| # | Beat |
|---|---|
| P1.1 | Implementation realises Ch 4 architecture in code; depth distribution mirrors Ch 4 |
| P1.2 | Implementation status labelled honestly: implemented and tested · implemented validation pending · architecturally specified but not yet wired · deferred/future |
| P1.3 | Manager realises BACAB in code; three deterministic gates as concrete controller logic (Listing 5.1) |
| P1.4 | Copilot ships through v1 (legacy) + v2 (trust-boundary) lanes; v2 = FastIntake/Planner/Validator/Factory/Path Registry/Escalation Gate; first slice ships Path 1/4/8 |
| P1.5 | Single-construction discipline enforced by **anti-drift tests in copilot pytest suite** (per W-2 / W-6 — NOT CI; copilot has no CI workflow). Path Registry reader allowlist + FastIntake path-range invariant similarly **architectural invariants protected by anti-drift tests** |
| P1.6 | Intelligence + UI at integration/foundation level; cross-service paths scope-honestly named with limits (per W-5, W-8) |

## P2. Required Identifiers and Concepts

**P2.1 — Toolchain (T5.1):** Python 3.11 · FastAPI 0.115 · SQLAlchemy 2 · Pydantic 2 (backend); Next.js 15 · React 18 · TypeScript · Tailwind · shadcn/ui (frontend); PostgreSQL (manager + intelligence) · SQLite (copilot dev-mode); Azure OpenAI deployment via env vars; Docker per service; docker-compose for manager + intelligence; **no compose for copilot, no unified root compose**; Git polyrepo-in-monorepo.

**P2.2 — BACAB folders:** routes · controllers · datasources · translators · connectors (active); models · schemas · config · utils (support). Discipline rules per Ch 4 O2.2.

**P2.3 — Manager 3 tables + 3 gates + atomic advance:** `rfq` · `workflow` · `rfq_stage`. Gates: mandatory-field, blocker, transition-validity. Atomic advance (per W-1): current stage complete with timestamp · next stage activated · RFQ progress recomputed · **lifecycle timestamps and persisted stage state updated** (NOT "status history entry").

**P2.4 — Manager 4 supporting families:** Subtasks (soft-delete, FR-MGR-08); Notes (append-only, no PUT/DELETE — architectural defense); Files (workbook type designated; manual/direct trigger to intelligence; **autonomous event-bus consumer NOT wired** per W-5); Reminders (manual + rule-based; **dispatch is log-only**).

**P2.5 — Manager analytics:** Implemented (pipeline, win-rate, by-client). **Deferred (do not claim):** margin analysis, estimation accuracy.

**P2.6 — Manager hardening:** Structured logging w/ correlation IDs · readiness probe + metrics (NFR-OPS-02) · Alembic migrations · input validation · Postman collection (existence; recorded execution → Ch 6 caveat) · **Manager service IS CI-enforced** per W-2; copilot/intelligence/frontend have NO CI workflow.

**P2.7 — Copilot v1/v2 lanes:** v1 = legacy; **frontend still consumes v1 for thread lifecycle**; v2 = trust-boundary lane serves actual conversational exchanges; migration of frontend thread mgmt to v2 is future scope.

**P2.8 — Copilot pipeline stages:** FastIntake → LLM Planner → PlannerValidator → ExecutionPlanFactory → Resolver → Access (manager-mediated) → Memory Load → Tool Executor → Evidence Check → Context Builder → Compose (with Path 4 deterministic renderer when LLM bypassed) → Guardrails → Judge → Finalizer → Persist.

**P2.9 — Copilot first vertical slice:** Path 1 (FastIntake-classified trivial; bypasses Tool Executor + Judge); Path 4 (RFQ-grounded operational, demo-defining); Path 8 family (5 sub-cases: 8.1 unsupported, 8.2 out-of-scope, 8.3 ambiguous target, 8.4 access denied/target missing, 8.5 insufficient evidence). Paths 2/3/5/6/7 route via Escalation Gate to Path 8.1.

**P2.10 — ExecutionPlanFactory three entry points + 3 anti-drift checks:** `build_from_intake` · `build_from_planner` · `build_from_escalation` (cannot fail). **Three architectural invariants protected by anti-drift tests in copilot pytest suite** (per W-2 / W-6 — NOT "CI-enforced"): (1) single-construction (no `TurnExecutionPlan` outside factory); (2) registry-reader allowlist (only Factory + Escalation Gate may import Path Registry); (3) FastIntake path-range invariant.

**P2.11 — Composition stages:** Memory (capture-only; **two extensions explicitly NOT IMPLEMENTED** per W-4: injection into prompts; future episodic-memory extension); Guardrails (evidence/scope/shape; deterministic; failure → Escalation Gate); Judge ("architectural equivalent of code review for LLM output: does not produce content, inspects content"; triggers: fabrication/scope drift/forbidden inference).

**P2.12 — Escalation Gate failure-trigger → Path 8 mapping:** target resolution / access denial → 8.4; confidence threshold / missing intent → 8.1; out-of-domain → 8.2; ambiguous target → 8.3; empty evidence / guardrail failure / negative Judge → 8.5. **Single place in codebase where mappings live.**

**P2.13 — Intelligence service:** Implemented: MR package parser (16-section); workbook parser (36-sheet); cross-check/anomaly surfacing (FR-INT-04). Partial/deferred: briefing (partial, demo-narrative-level); intake pipeline (manual/direct flows; **autonomous event-driven manager-to-intelligence flow is deferred** per W-5); manager integration (read-only, trigger-based); **copilot integration NOT IMPLEMENTED**; predictive intelligence (future).

**P2.14 — UI service (per W-8):** **`rfq_ui_ms` = implemented interface layer with live API support and demo/mock fallback; browser E2E validation pending.** Screens: RFQ list/portfolio, RFQ detail (lifecycle + subtasks/notes/files + reminders + intelligence panel), dashboard (executive KPI cards). Conversational entry: copilot drawer (RFQ-bound), copilot page (portfolio mode). Dev-mode: live API + mock fallback via config switch. Deferred/partial: no production login; NOT containerized; no browser E2E; frontend thread mgmt on v1 lane.

**P2.15 — Cross-service paths:** Manager → intelligence: manual/direct trigger (autonomous deferred per W-5). Copilot → intelligence: NOT wired (Path 5 deferral).

**P2.16 — LaTeX label keys:** `tab:toolchain` (T5.1); `fig:manager_structure` (F5.1, optional/appendix); `lst:advance_stage` (Listing 5.1); `fig:copilot_pipeline` (F5.2, flagship redesign); `lst:factory_signature` (Listing 5.2); `fig:ui_screen` (F5.3).

## P3. Required Tables, Figures, and Code Listings

| Item | Status | Notes |
|---|---|---|
| T5.1 — Toolchain | Must remain | ~13 rows; may compress to ~8–10 |
| **Listing 5.1 — `advance_stage` controller** | Must remain in main | Per amendment 3: SHORT excerpt only; closing comment uses W-1 wording |
| **Listing 5.2 — `ExecutionPlanFactory` signature** | Must remain in main | Per amendment 3: SHORT excerpt only; three public entry points + `_resolve_policy` boundary |
| **F5.2 — Turn pipeline (FLAGSHIP)** | Must remain in main | Distinguishes deterministic stages from LLM invocations by color |
| F5.3 — UI screenshot | Must remain in main | RFQ detail + copilot drawer |
| F5.1 — Manager folder structure | Tier 3 / drop or appendix | 2 lines of prose suffice |

## P4. Specific Phrasings That Must Survive

- **P4.1 — Audit-honesty framing of implementation status (§5 introduction)**: 4-tier vocabulary discipline must remain.
- **P4.2 — Reminder dispatch is log-only (§5.2)**.
- **P4.3 — Notes endpoint architectural-defense framing**: "architectural defense, not a missing feature".
- **P4.4 — v1/v2 lane reality (§5.3)**: frontend still consumes v1 for thread lifecycle; v2 serves actual conversational exchanges; migration future scope.
- **P4.5 — Path 1/4/8 first-vertical-slice + Paths 2/3/5/6/7 routing**: explicit framing.
- **P4.6 — Single-construction discipline as architectural invariants protected by anti-drift tests (per W-2 / W-6)**: NOT "CI-enforced".
- **P4.7 — Memory: capture-only + future-episodic framing (per W-4)**: both deferred extensions explicit.
- **P4.8 — Judge-as-code-review framing**: "Judge is architectural equivalent of code review for LLM output: does not produce content, inspects content".
- **P4.9 — Escalation Gate "no parallel error path" framing**.
- **P4.10 — UI status framing (per W-8)**: "implemented interface layer with live API support and demo/mock fallback; browser E2E validation pending".
- **P4.11 — Cross-service integration limits (§5.6)**: both paths' limits explicit (W-5).

## P5. Scope-Honesty Statements

| # | Statement |
|---|---|
| P5.1 | Manager has CI; copilot/intelligence/frontend have NO CI workflow |
| P5.2 | Reminder dispatch log-only |
| P5.3 | Manager analytics: pipeline/win-rate/by-client implemented; margin/accuracy deferred |
| P5.4 | Dedicated audit-history surface NOT implemented (per P-8) |
| P5.5 | Copilot v1 preserved for frontend thread lifecycle; v2 serves turns |
| P5.6 | Memory: capture-only; injection deferred + future episodic-memory extension (per W-4) |
| P5.7 | Paths 2/3/5/6/7 route via Escalation Gate to Path 8.1 |
| P5.8 | UI: no production login, no containerization, no browser E2E, frontend thread mgmt still on v1 |

**Forbidden in Ch 5 (per amendment 2 — implementation chapter implements; doesn't pre-cite Ch 6 evidence):** validation numbers (per P-1, Ch 6 only); test counts/file names/anti-drift test names (per P-2, Ch 6 only); "CI-enforced" for copilot/intelligence/frontend (per W-2); "status history entry written" (per W-1); "long-term episodic memory" framed as imminent (per W-4); "strict guarantees / ensures / fully production-ready / fully integrated" (per W-3, W-7); compound names (per N-1); Ch 4 conceptual material restated.

**Preferred bridging wording (per amendment 2):** "implemented in code and validated in Chapter 6" rather than detailed test-validation claims in Ch 5.

## P6. Naming-Canon Enforcement

Per N-1 to N-4. BACAB-pattern attribution to host firm conventions appears in §5.2.

## P7. v0 Errata to Fix

- **P7.1 — Cross-chapter renumbering:** "Chapter 2" → Ch 3, "Chapter 3" → Ch 4, "Chapter 5" → Ch 6 throughout v0 Ch 4
- **P7.2 — Intra-chapter §-references** re-mapped to v1 §5.x
- **P7.3 — Internal CI overclaim reconciliation (per W-2):** v0 lines 191/202/244 describe copilot anti-drift checks as "CI" — soften to "anti-drift test in copilot pytest suite"
- **P7.4 — Status-history overclaim (per W-1):** v0 line 148 "append-only status history" softened to "lifecycle timestamps, persisted stage state, append-only notes, non-destructive update semantics"
- **P7.5 — Episodic memory wording (per W-4):** v0 line 233 "long-term episodic summarization" → "future episodic-memory extension"
- **P7.6 — UI status wording (per W-8)**
- **P7.7 — Manager-to-intelligence wording (per W-5)**
- **P7.8 — Macro resolution check**

## P8. What May Be Compressed

- §4.1 toolchain narrative → ~50% (table does work)
- §4.3.1 BACAB-in-code → ~30% → 1 paragraph
- §4.3.3 supporting resources (4 paragraphs) → 1 paragraph each (~60%)
- §4.3.4 statistics → ~50%
- §4.3.5 containerization + hardening → ~50%
- §4.4 v1/v2 lane intro → 1 paragraph (~60%)
- §4.4.1 turn pipeline → ~50%; bullet-style stage list
- §4.4.2 Path Registry & Planner → ~40%
- §4.4.4 memory/guardrails/Judge → tight paragraph each (~50%); P4.7, P4.8 wording preserved
- §4.5 intelligence + UI → ~50%; partial-status enumerations compressed but each item visible
- Multi-screen UI tour → drop entirely
- Manager folder structure narrative + Fig 5.1 → drop or appendix

## P9. Content That Must NOT Move to Appendix

- Toolchain table (T5.1)
- **Listing 5.1 (advance_stage)** — strongest concrete proof of architecture-in-code
- **Listing 5.2 (factory signature)** — companion proof of single-construction
- **F5.2 turn pipeline (flagship)**
- F5.3 UI screenshot
- Manager three-gate controller realisation paragraph
- v1/v2 lane reality + frontend thread mgmt on v1
- Path 1/4/8 + Paths 2/3/5/6/7 routing
- Three anti-drift checks (P2.10, per W-2/W-6)
- Memory capture-only + 2 deferred extensions (per W-4)
- Cross-service integration status (§5.6)
- All 8 scope-honesty statements (P5.1 → P5.8)

## P10. Verification Procedure

**Pass 1 — Structural check.** Six narrative beats (P1.1 → P1.6) in order. Toolchain (T5.1), BACAB folders, 3 manager tables + 3 gates + atomic advance with W-1 wording, 4 supporting families, v1/v2 lane reality, Path 1/4/8 + Paths 2/3/5/6/7 routing all present. Naming canon.
**Pass 2 — Cross-reference renumbering.**
**Pass 3 — Code listing fidelity.** Listing 5.1 closing comment uses W-1 wording (NOT "status history entry"). Three gates in correct order. Listing 5.2 has three public entry points + `_resolve_policy`. Both render as actual code blocks (per amendment 3 — short excerpts only).
**Pass 4 — Cross-chapter amendment compliance check.** Grep "continuous integration" / "CI" — only manager-service occurrences permitted (per W-2). Grep "status history entry" — zero (per W-1). Grep "long-term episodic memory" — zero as imminent claim (per W-4). Grep "demonstration only" / "demo-only" applied to UI — replaced with W-8 wording. Grep "synchronous trigger in present implementation" — replaced with W-5 wording.
**Pass 5 — Scope-honesty check.** All 8 scope-honesty statements (P5.1 → P5.8) appear. No validation numbers (per P-1), no individual anti-drift test names (per P-2), no Ch 4 conceptual material restated. Audit-honest framing (P4.1) in §5 introduction.
**Pass 6 — Page allocation enforcement (per S-3, amendment 4).** §5.3 must remain the largest or second-largest section of Ch 5 and must preserve enough depth to explain the implemented copilot pipeline, factory discipline, Path 1/4/8 scope, guardrails, Judge, Finalizer, Escalation Gate. Practical test: a reader who has read Ch 4 v1 must be able to verify that the implementation matches the architecture; a reader who has not read Ch 4 v1 cannot understand the implementation from Ch 5 alone (acceptable — Ch 4 v1 is the prerequisite).

---

# Chapter 6 v1 — Validation, Results, and Discussion

**Chapter target in v1:** 10–12 pages (compressed from ~25 pp v0 Ch 5). Per S-4 / amendment 1: "Chapter 6 must remain one of the strongest chapters and must not be over-compressed. It should normally target 10–12 pages, but final acceptance depends on evidence completeness and clarity, not page count alone."
**Subsections:** 6.1 Validation Strategy and Five Evidence Classes · 6.2 Manager Service Validation · 6.3 Copilot Service Validation · **6.4 Trust-Boundary Verification via Anti-Drift Tests (NEW promoted standalone, per S-1)** · 6.5 Intelligence Service Validation · 6.6 Frontend and Cross-Service Integration Validation · 6.7 Business Impact Mapping · 6.8 Limitations · 6.9 Future Work.

**This is the report's defensibility crown jewel. Cut LEAST aggressively.**

## Q1. Load-Bearing Narrative Arc (six ordered beats)

| # | Beat |
|---|---|
| Q1.1 | Five complementary evidence classes: service-level pytest · architectural-invariant verification (anti-drift) · scenario-level (smoke + pipeline) · integration · business-impact analysis |
| Q1.2 | Limits stated up front: CI for manager only · manager pytest on SQLite quality-gate · copilot LLM stages on FakeLlmConnector · no browser E2E |
| Q1.3 | Service-level validation in order of strength: manager → copilot → trust-boundary verification (visible §6.4) → intelligence → frontend → integration |
| Q1.4 | Trust-boundary verification has visible standalone §6.4 (per S-1); 18 anti-drift tests named at category level |
| Q1.5 | Business impact: 12 PP-NN mapped to capabilities; 2/7/3 split is the headline finding |
| Q1.6 | Honest limitations in 5 categories + three-tier future work (Near-term validation hardening / Medium-term architecture completion / Long-term Pillar 4 predictive) |

## Q2. Required Identifiers and Numbers (per P-1, Ch 6 only)

**Q2.1 — Exact validation numbers (audit-snapshot baseline; rewriter must re-run pytest pre-submission per amendment 2 and update if drifted):**
- Manager: **259 pytest tests, all passed** ("259 passed, 121 warnings in 25.29s"); 27 test files
- Copilot: **636 pytest tests, all passed** ("636 passed, 3 warnings in 4.84s"); 47 test files
- Copilot pipeline: 216 functions; smoke: 98 functions; anti-drift: **18 functions**; other: 304 functions
- Intelligence: **118 tests** total: 64 passed + 48 fixture-dependent + 6 skipped
- Frontend: **12 source-contract scripts**: 11 passed, 1 assertion drift
- 216 + 98 + 18 + 304 = 636 sum check

**Q2.2 — 18 anti-drift tests (named at category level in §6.4; full filenames may go to light appendix):** factory-only `TurnExecutionPlan` construction · Path Registry reader allowlist · FastIntake anchored-regex · no-LLM-SDK in deterministic stages · LLM structured-output enforcement · no-v3-references · memory-policy load-bearing · Batch 10 no-history-injection (and others; full list in light appendix per P-7).

**Q2.3 — Five evidence classes** named in §6.1.

**Q2.4 — 12 pain points (PP-01 → PP-12) in T6.5 with 3-level vocabulary:**
- **Addressed (2):** PP-01, PP-08
- **Partially addressed (7):** PP-02, PP-03, PP-05, PP-06, PP-07, PP-11, PP-12
- **Not yet addressed (3):** PP-04, PP-09, PP-10

**Q2.5 — 9 scenario families** in §6.3: FastIntake trivial; RFQ-grounded Path 4; By-code RFQ lookup; Manager-core Path 4 full pipeline; Guardrail behaviour; Path 8 safe fallback; Ownership enforcement; Known-thread requirement; Execution record persistence.

**Q2.6 — 6 integration paths in T6.4:** UI↔manager (Demo); UI↔copilot (Demo; thread mgmt v1, turn v2); UI↔intelligence (Demo); Copilot↔manager (Tested via test double + manual scenario); **Manager↔intelligence (manual/direct trigger; autonomous event-driven flow deferred per W-5)**; **Copilot↔intelligence (NOT IMPLEMENTED — Path 5 deferral)**.

**Q2.7 — 5 limitations categories in §6.8:** Validation-Methodology · Implementation-Surface · Architecture-Scope · Working Memory and Conversation Continuity (per W-4 — future episodic-memory extension) · Honest Statement of Risk (validation dataset is "highest-priority hardening item").

**Q2.8 — Three-tier future work in §6.9:** Near-Term (Validation Hardening) · Medium-Term (Architecture Completion) · Long-Term (Pillar 4 / Predictive).

**Q2.9 — LaTeX label keys:** `tab:validation_summary` (T6.1); `lst:manager_tests` (Listing 6.1); `tab:manager_validation` (T6.2); `lst:copilot_tests` (Listing 6.2); `tab:copilot_tests` (T6.3); `tab:integration` (T6.4); `tab:business_impact` (T6.5).

## Q3. Required Tables, Figures, and Code Listings

| Item | Status | Notes |
|---|---|---|
| T6.1 — Validation summary | Must remain | 5 rows (Manager/Copilot/Intelligence/Frontend/Integration) with Evidence/Result/Caveat |
| Listing 6.1 — Manager pytest invocation | Must remain | Per S-7: SHORT 4-line form |
| T6.2 — Manager per-area | Must remain | 8 rows; "PostgreSQL pending" / "Postman pending" / "audit-history not implemented" rows non-negotiable |
| Listing 6.2 — Copilot pytest invocation | Must remain | Per S-7: SHORT 4-line form |
| T6.3 — Copilot test breakdown | Must remain | 4 categories + total; 216+98+18+304=636 sum |
| T6.4 — Integration paths | Must remain | 6 rows; per-path status |
| T6.5 — Business impact | Must remain | All 12 PP-NN; 2/7/3 split |

## Q4. Specific Phrasings That Must Survive

- **Q4.1 — Limits-up-front paragraph (§6.1)**: 4 explicit statements (CI-only-manager · SQLite · FakeLlmConnector · no browser E2E).
- **Q4.2 — FakeLlmConnector framing (§6.3)**: "deterministic test double … permits deterministic and reproducible verification of pipeline's structural behaviour … but does not validate language-model response quality of deployed model on production-scale traffic".
- **Q4.3 — Anti-drift framing (§6.4 per W-6)**: "architectural invariants protected by anti-drift tests" — NOT "anti-drift tests guarantee" / "ensure".
- **Q4.4 — Two qualifications, no other qualifications (§6.3)**: "with those two qualifications acknowledged, the validation is the strongest in the project".
- **Q4.5 — Intelligence fixture-dependent framing (§6.5)**: "environmental absence … rather than parser regressions".
- **Q4.6 — Frontend "assertion drift" framing (§6.6)**: "assertion drift … not a runtime regression … maintenance item rather than validation gap".
- **Q4.7 — Three observations on business impact (§6.7)**: PP-01 + PP-08 substantively addressed by operational backbone alone; 7 partially addressed ("partial addressing is not a weakness here; consequence of the strategic pivot"); 3 not yet addressed within future scope.
- **Q4.8 — Highest-priority hardening item (§6.8)**: "limited scale of validation dataset … is most consequential validation gap … highest-priority hardening item for any subsequent work".
- **Q4.9 — Working-memory deferred-extensions framing (§6.8 per W-4)**: "Memory injection and future episodic-memory extension are recognized as future extensions to the memory architecture".
- **Q4.10 — Eight trust boundaries hold "in measured behaviour" closing (§6.9 / Ch conclusion)**: "produced a platform whose foundations are sound, whose innovation is verifiable, and whose direction is established".

## Q5. Scope-Honesty Statements / Required Caveats (defensibility crown jewels — all 12 must appear)

| # | Caveat |
|---|---|
| Q5.1 | Manager pytest on SQLite quality-gate; PostgreSQL hardening direction |
| Q5.2 | Postman collection exists; recorded Newman execution NOT in current evidence |
| Q5.3 | Manager service is only service with CI; copilot/intelligence/frontend have working test suites but no CI workflow |
| Q5.4 | Copilot LLM stages exercised via FakeLlmConnector test double; no live-model regression |
| Q5.5 | No curated benchmark dataset; smoke + pipeline tests function as automated golden scenarios |
| Q5.6 | Anti-drift tests are architectural invariants protected by tests, not guarantees (per W-6) |
| Q5.7 | Intelligence: 64 fixture-independent passing; 48 fixture-dependent failing with `FileNotFoundError` (`tests/local_fixtures/` gitignored); 6 skipped by design; failures NOT parser regressions |
| Q5.8 | Frontend: 11 of 12 passing; 1 assertion drift (maintenance item); no browser E2E |
| Q5.9 | Integration: demonstration-oriented, not test-automated |
| Q5.10 | Manager → intelligence: manual/direct trigger; autonomous event-driven deferred (per W-5); copilot → intelligence: NOT implemented (Path 5 deferral) |
| Q5.11 | Copilot first vertical slice: Path 1/4/8 shipped; Paths 2/3/5/6/7 escalate (architecturally correct, not degraded) |
| Q5.12 | Working memory capture-only; injection deferred + future episodic-memory extension explicitly NOT implemented (per W-4) |

**Forbidden in Ch 6 (per cross-chapter amendments):** "guarantees" wording for anti-drift (per W-6); "status history entry written" (per W-1); "CI-enforced" for non-manager services (per W-2); "long-term episodic memory" framed as imminent (per W-4); "synchronous trigger in present implementation" (per W-5); "fully production-ready / fully integrated / ensures" (per W-3, W-7); compound names (per N-1); overclaiming intelligence fixture-dep failures as parser regressions; overclaiming frontend assertion drift as runtime failure.

## Q6. Naming-Canon Enforcement

Per N-1 to N-4. **`SA-AYPP-6-MR-022` and `IF-25144` are permitted in Ch 6** (specifically §6.5 fixture-dependent framing) — Ch 6 is the validation context for these fixtures.

## Q7. v0 Errata to Fix

- **Q7.1 — Cross-chapter renumbering:** "Chapter 2" → Ch 3, "Chapter 3" → Ch 4, "Chapter 4" → Ch 5 throughout v0 Ch 5; intra-chapter §-references → v1 §6.x. The dangling §5.5 anti-drift cross-reference at v0 line 97 must point to **v1 §6.4**.
- **Q7.2 — Anti-drift section creation (per S-1, amendment 3):** v0 promises but does not deliver dedicated anti-drift section; v1 §6.4 is the NEW visible standalone section. Open with W-6 framing; enumerate 18 categories (per Q2.2); map invariant categories to 8 trust boundaries from §4.4 v1; close with connection to single-construction discipline.
- **Q7.3 — File-path references** must be confirmed to still exist (manager CI workflow, Postman collection, scenario stack script, smoke demo doc, seed manifests, intelligence local_fixtures/).
- **Q7.4 — Re-run pytest before submission (mandatory per amendment 2 / P-1).** Latest verified results replace audit-snapshot numbers if changed. Update T6.1, T6.3, prose, conclusion accordingly.
- **Q7.5 — Macro resolution check**

## Q8. What May Be Compressed

- §5.1 introductory prose around 5 evidence classes → ~30% (limits-up-front paragraph Q4.1 untouched)
- §5.2 manager subsections → ~30%
- §5.3 prose around test categories → ~40%
- §5.4 (v0) Golden Scenarios — 9 families → tight bulleted run (~40%)
- §5.5 (v0) integration prose → ~40%; T6.4 carries structure
- §5.5.2 demo evidence → ~50%
- §5.5.3 intelligence validation → ~30%; fixture-dependent framing (Q4.5) non-negotiable
- §5.6 closing summary → 2–3 sentences
- §5.7 "Reading the Mapping" three observations → ~40%; all 3 (Q4.7) remain
- §5.8 Risk paragraph → drop one sentence; Q4.8 framing survives
- Listings 6.1 + 6.2 (already short per S-7); no compression
- Full anti-drift catalogue (18 named filenames, one-line each) → light appendix per P-7
- Detailed Postman walkthrough specs → drop or 1-line mention
- §5.9 Conclusion → ~50%

## Q9. Content That Must NOT Move to Appendix

- Five evidence classes (Q2.3) named in §6.1
- Limits-up-front paragraph (Q4.1)
- All exact validation numbers (Q2.1) — exist nowhere else in v1 report (per P-1)
- T6.1, T6.2, T6.3, T6.4, T6.5
- §6.4 trust-boundary verification as visible standalone (per S-1)
- 18 anti-drift test categories named in §6.4
- 2/7/3 split summary + three observations (Q4.7)
- All 5 limitations categories (Q2.7)
- Highest-priority-hardening-item statement (Q4.8)
- Three-tier future work (Q2.8)
- All 12 scope-honesty caveats (Q5.1 → Q5.12)

## Q10. Verification Procedure

**Pass 1 — Structural check.** Six narrative beats (Q1.1 → Q1.6) in order. §6.4 is top-level numbered section, not folded into §6.6. Naming canon.
**Pass 2 — Cross-reference renumbering (Q7.1).** Dangling v0 §5.5 → v1 §6.4.
**Pass 3 — Number freshness check (Q7.4 — per P-1 / amendment 2).** Re-run pytest pre-submission. Update T6.1, T6.3, prose, conclusion if drifted. 216+98+18+304 = current copilot total.
**Pass 4 — Caveat-preservation check (defensibility gate).** Grep for each of 12 scope-honesty caveats (Q5.1 → Q5.12). All present. Specific grep targets: "FakeLlmConnector" / "deterministic test double"; "SQLite" / "quality-gate"; "fixture-dependent" / "FileNotFoundError"; "no browser-level" / "no Playwright" / "no E2E"; "log-only"; "capture-only" / "future episodic-memory extension"; "Path 8" / "Path 5 deferral" / "not implemented"; "highest-priority hardening item".
**Pass 5 — Cross-chapter wording-rule compliance check.** Grep for forbidden wording per registry: "guarantees" referring to anti-drift (zero per W-6); "strict guarantees" (zero per W-3); "CI-enforced" applied to copilot/intelligence/frontend (zero per W-2); "status history entry" (zero per W-1); "long-term episodic memory" framed as imminent (zero per W-4); "synchronous trigger in present implementation" (zero per W-5).
**Pass 6 — Cross-reference + identifier check.** All 12 PP-NN in T6.5 with three-level status. FR identifiers in chapter prose match Ch 3 FR table. LaTeX label keys (Q2.9) unchanged.
**Pass 7 — Page allocation enforcement (per S-4 / amendment 1 — flexible).** Ch 6 should normally target 10–12 pages, but **final acceptance depends on evidence completeness and clarity, not page count alone**. §6.7 + §6.8 + §6.9 together must occupy at least 3 pp (defensibility close). §6.4 must occupy at least 1 pp.

---

## End of file
