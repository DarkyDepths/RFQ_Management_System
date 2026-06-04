# PFE Report Handoff — Read Me First

## Purpose of this folder

This folder contains the context required to transform the current report v0 into a shorter, stronger, jury-ready v1 version.

The current v0 report is a full internal knowledge version. It is technically rich but too long for the final PFE constraint.

The supervisor validated the engineering structure but requested one major academic correction:

- Add a dedicated State of the Art / Technological Background chapter.
- Reduce the report to 50–70 pages maximum.
- Preserve the separation between Architecture and Implementation.
- Preserve the strong Validation chapter.
- Preserve traceability, ADRs, and scope honesty.

## Project identity

The platform currently uses **Itqan** as a working name, but the name is not fully frozen yet.

The report title is also provisional and can be improved if a better academic and professional formulation is found.

Current working title:

**Design and Implementation of Itqan: An AI-Enabled RFQ Lifecycle Intelligence Platform for Industrial Estimation Process Optimization**

Claude Code may suggest improvements to the platform name or report title, but must explain the rationale and must not apply naming changes directly without approval.

## Main narrative to preserve

The report must preserve this story:

1. GHI initially requested BOQ automation.
2. The audit showed that direct BOQ automation was not feasible or safe because estimation expertise was not codified and historical data was not structured.
3. The project pivoted from BOQ automation to RFQ lifecycle intelligence.
4. The platform was designed around:
   - RFQ lifecycle orchestration,
   - structured tracking,
   - intelligence foundation,
   - evidence-grounded conversational assistance.
5. `rfq_manager_ms` is the operational backbone.
6. `rfq_copilot_ms` is the innovation centerpiece through its trust-bound conversational architecture.
7. `rfq_intelligence_ms` and `rfq_ui_ms` support the platform as foundation/integration layers.
8. Validation must prove what is implemented, what is partial, and what remains future work.

## Important rule

Do not treat v0 as final.

v0 is the full draft.

v1 must be compressed, academically balanced, and aligned with the supervisor’s page limit.

## Source hierarchy

When sources disagree, use this order:

1. Current repository code and tests.
2. Implementation and validation audits.
3. Current v0 report chapters.
4. Frozen architecture documents.
5. Microservice-specific documentation.
6. Reference PFE reports.

Microservice documentation may be outdated. It must be checked against code and audits.

## Scope honesty vocabulary

Use these labels consistently:

- implemented and tested
- implemented, validation pending
- partial
- demo/mock
- documented only
- deferred/future
- not found / unclear

Never claim something is implemented, validated, or integrated unless the code or validation audit supports it.

## Claude Code role

Claude Code should first operate in **PLAN MODE ONLY**.

This does not mean Claude Code is only a formatting assistant.

Claude Code is expected to act as a repo-aware report reviewer and planning assistant. It may:

- critique the current v0 structure,
- propose a better v1 structure,
- propose a State of the Art chapter,
- suggest what to keep, compress, move, or delete,
- propose figures, tables, screenshots, and appendices,
- identify contradictions between the report, code, audits, and documentation,
- suggest better naming or title options,
- identify risks caused by compression.

However, Claude Code should not modify report files during the first pass.

The first output must be a transformation plan from v0 to v1:

- new 6-chapter TOC,
- page budget,
- what to keep,
- what to compress,
- what to move,
- what to delete,
- what becomes appendix material,
- proposed State of the Art structure,
- essential figures and tables,
- risks and questions before execution.

After the plan is reviewed and approved, Claude Code may then execute changes step by step.