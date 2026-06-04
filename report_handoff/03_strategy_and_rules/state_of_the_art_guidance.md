# State of the Art Guidance

## Purpose

The supervisor required a dedicated State of the Art / Technological Background chapter.

This chapter is missing from v0 and must be added in v1.

The goal is not to add generic AI theory. The chapter must explain the existing technological and academic landscape that justifies the proposed platform.

## Role of the chapter

The State of the Art chapter should answer:

1. What technologies and concepts does the project rely on?
2. What existing solutions or approaches already exist?
3. Why are they not sufficient for the specific GHI RFQ lifecycle problem?
4. Why is the proposed platform technically justified?
5. Why is the trust-bound copilot architecture relevant and innovative?

## Proposed chapter title

Chapter 2 — State of the Art and Technological Background

The title can be improved if a better academic formulation is proposed.

## Suggested structure

### 2.1 Introduction

Explain why this chapter is necessary:
- RFQ lifecycle optimization is not only a business problem;
- it touches enterprise systems, workflow systems, BI, and AI copilots;
- before presenting requirements and architecture, the report must position the project against existing concepts and solutions.

### 2.2 Digitalization of RFQ and Industrial Estimation Processes

Cover:
- RFQ process management;
- quotation workflows;
- industrial estimation constraints;
- limits of manual Excel-based processes;
- need for lifecycle traceability.

### 2.3 Existing Enterprise Solutions

Cover:
- ERP systems;
- CPQ tools;
- RFQ management tools;
- BI dashboards;
- workflow/BPM systems.

Expected conclusion:
These systems support parts of the problem, but they do not fully solve the combination of industrial RFQ lifecycle tracking, document intelligence, evidence-grounded conversational access, and future learning.

### 2.4 AI for Enterprise Decision Support

Cover:
- large language models;
- retrieval-augmented generation;
- conversational agents;
- AI copilots;
- AI-assisted decision support.

Expected conclusion:
LLMs are useful for interaction and synthesis, but they are unsafe in industrial workflows if they are not grounded, bounded, and verified.

### 2.5 Trust, Evidence, and Hallucination Risks

Cover:
- hallucination risk;
- evidence grounding;
- source-of-truth strategy;
- access control and data leakage;
- why generic LLM agents are risky when operational truth matters.

Expected conclusion:
A copilot for RFQ lifecycle intelligence must not behave like a generic chatbot. It must separate language fluency from operational authority.

### 2.6 Positioning of the Proposed Platform

Compare:
- ERP vs Itqan-like platform;
- CPQ/RFQ tools vs Itqan-like platform;
- BI dashboards vs Itqan-like platform;
- naive RAG vs trust-bound copilot;
- generic agents vs trust-bound copilot.

Expected conclusion:
The project is positioned as an RFQ Lifecycle Intelligence Platform with a trust-bound conversational layer, not as a generic chatbot, ERP replacement, or BOQ automation system.

### 2.7 Conclusion

Summarize:
- why the state of the art is insufficient;
- why a platform approach is justified;
- why the manager service and copilot architecture answer the identified gap.

## Important constraints

- Keep the chapter concise: target 8–9 pages maximum.
- Avoid generic textbook explanations.
- Do not over-explain LLMs, RAG, or microservices.
- Every concept must connect back to the Itqan project.
- Use tables and diagrams where they reduce prose.
- Do not copy from reference reports.
- Do not claim Itqan is better than commercial products without careful wording.
- Use cautious language: “addresses a gap”, “is positioned as”, “combines”, “supports”, rather than absolute claims.

## Suggested visuals

Claude Code may propose better visuals, but likely useful visuals include:

1. A comparison table:
   ERP / CPQ / RFQ tools / BI / Generic LLM assistant / Proposed platform

2. A diagram:
   From manual RFQ process to AI-enabled lifecycle intelligence

3. A comparison table or diagram:
   Naive RAG vs generic LLM agent vs trust-bound copilot

Use only the essential visuals to stay within the 50–70 page limit.

---

## Reconciliation note (2026-05-10)

This file is the original SoA chapter seed. It has been **refined and operationalized** in:

- `citation_map_v1.md` — Phase β verified citation map for Ch 2 SoA: 17 verified citations across §2.2 (industrial RFQ/CPQ), §2.3 (microservices/layered patterns), §2.4 (LLM conversational taxonomy), §2.5 (hallucination/grounding/safety), §2.6 (document intelligence). Includes 2 removed slots and 2 softened-claim slots with documented prose framings.
- `bibliography_entries_v1.md` — 17 draft `\bibitem{}` entries ready for use.
- `chapter_checklists_v1.md` (Chapter 2 v1 SoA creation checklist section) — refined section structure (§2.1 Introduction · §2.2 Industrial Quotation and RFQ Management Systems · §2.3 Microservices and Layered Architecture Patterns · §2.4 LLM-Powered Conversational Systems: A Taxonomy · §2.5 Grounding, Hallucination, and AI Safety Concerns · §2.6 Document Intelligence in Engineering Contexts · §2.7 Comparative Analysis and Positioning); R1 mission rules · R2 per-section scope · R3 must-cover concepts · R4 anti-pattern list · R5 forward-pointer mapping · R6 citation discipline · R7 visuals · R8 verification procedure.

The original "Suggested structure" in this file (§2.1 through §2.7 with different titles) was an early draft. The operational structure is in `chapter_checklists_v1.md`. The "Important constraints" (concise, no generic theory, every concept connects to Itqan, cautious wording) are preserved in the operational checklist as the chapter's discipline floor.

The "Suggested visuals" list (comparison table, evolution diagram, naive-RAG vs LLM-agent vs trust-bound copilot diagram) has been operationalized as Table 2.1 (Comparative positioning matrix) and Figure 2.1 (Conversational AI architecture taxonomy) in the chapter checklist.