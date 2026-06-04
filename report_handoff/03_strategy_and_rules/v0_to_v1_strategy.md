# Report v0 to v1 Strategy

## Current situation

The current report v0 is a full internal knowledge version. It contains the main project narrative, architecture, implementation, validation evidence, and business impact discussion.

However, it is too long for the final PFE constraint and it is missing a dedicated State of the Art / Technological Background chapter.

## Supervisor decision

The supervisor validated the engineering quality of the current structure, especially:

- the separation between Architecture and Implementation;
- the strong Validation chapter;
- the traceability matrix;
- the Architectural Decision Record approach.

The supervisor required one major correction:

- add a dedicated State of the Art / Technological Background chapter.

The supervisor also set a final report length target:

- 50 to 70 pages maximum.

## Transformation objective

Transform v0 into a shorter, stronger, academically balanced v1.

The goal is not only to add a chapter, but to compress and rebalance the whole report.

## Proposed v1 chapter structure

1. General Context and Business Problem
2. State of the Art and Technological Background
3. Requirements, Methodology, and Project Management
4. Conceptual and Technical Architecture
5. Implementation
6. Validation, Results, and Discussion

## Target page budget

Target total: around 60–68 pages of main content.

Suggested distribution:

- General Introduction: 1–2 pages
- Chapter 1: 7–8 pages
- Chapter 2 State of the Art: 8–9 pages
- Chapter 3 Requirements and Methodology: 8–9 pages
- Chapter 4 Architecture: 13–15 pages
- Chapter 5 Implementation: 9–11 pages
- Chapter 6 Validation: 10–12 pages
- General Conclusion: 1–2 pages

## Core narrative to preserve

The report must preserve this logic:

Audit revealed that BOQ automation was unsafe and infeasible under current data conditions. The project therefore pivoted to RFQ lifecycle intelligence. The platform provides a structured lifecycle backbone, an evidence-grounded conversational copilot, and a parsing/intelligence foundation for future predictive capabilities.

## Compression principles

### Keep

- BOQ to lifecycle intelligence pivot.
- Four-pillar vision.
- Manager service as operational backbone.
- Trust-bound copilot as innovation centerpiece.
- Evidence boundary.
- Implementation honesty.
- Validation numbers and caveats.
- Business impact mapping.
- Limitations and future work.

### Compress

- Long company and audit context.
- Long RFQ process explanations.
- Repeated explanations of the same architectural principles.
- Long methodology prose.
- Detailed implementation descriptions that duplicate architecture.
- Detailed validation explanations where a table is enough.

### Move to appendix

- Detailed use case descriptions.
- Selected Path Registry excerpts.
- Long prompt excerpts.
- Additional sequence diagrams.
- API/Postman details.
- Detailed test inventories.

### Avoid

- Generic AI theory not tied to Itqan.
- Copying structure/content from reference reports.
- Overclaiming implementation status.
- Expanding the report beyond 70 pages.

---

## Reconciliation note (2026-05-10)

This file remains the authoritative source for the v1 chapter structure (six chapters), the page budget (60–68 pp main body, 50–70 pp limit), and the compression principles (Keep / Compress / Move to appendix / Avoid).

The operational layer that applies these principles per chapter, plus the citation work for the new Chapter 2 (State of the Art), lives in:

- `citation_map_v1.md` — Phase β verified citation map (17 sources verified for Ch 2; 2 removed, 2 softened; full audit trail)
- `bibliography_entries_v1.md` — 17 draft `\bibitem{}` entries derived from the citation map
- `chapter_checklists_v1.md` — six chapter must-not-be-lost checklists with verification procedures
- `cross_chapter_wording_rules_v1.md` — accumulated naming-canon, wording-softening, content-placement, and structural rules

Note on the page budget: Ch 6 amendment 1 refines the Ch 6 page-count gate to be flexible — "Chapter 6 must remain one of the strongest chapters and must not be over-compressed. It should normally target 10–12 pages, but final acceptance depends on evidence completeness and clarity, not page count alone." The other chapter targets remain as listed above.