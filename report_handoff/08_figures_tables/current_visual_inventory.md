# Visual Strategy and Current Inventory — v0

## Purpose

The visual part of the report is not fixed yet.

Figures, tables, diagrams, screenshots, architecture maps, process flows, and comparison visuals are crucial for the final quality of the report. The current v0 contains placeholders and planned visuals, but these should not be treated as final.

Claude Code must act as a strong report-visual reviewer and propose the best possible visual strategy for a 50–70 page academic PFE report.

The goal is not to blindly generate every placeholder.

The goal is to decide which visuals best serve the jury’s understanding, the academic quality of the report, and the technical narrative of the project.

## Visual design tools already considered or used

The report may use visuals generated or refined with tools such as:

- Mermaid
- draw.io / diagrams.net
- Eraser.io
- Napkin.ai
- Cloudairy / Cloudinary-style visual assets if relevant
- Excalidraw
- manual LaTeX tables
- screenshots from the running platform
- exported architecture diagrams

Claude Code may recommend the best tool for each visual type.

## Important rule

The visual strategy is open for improvement.

Claude Code may propose:

- replacing a placeholder with a better diagram;
- merging two redundant visuals;
- deleting a weak visual;
- moving a detailed visual to the appendix;
- replacing long prose with a strong table;
- replacing a table with a more readable figure;
- adding a new visual if it is truly important;
- changing the order or placement of visuals;
- recommending screenshots where they add credibility;
- recommending no visual where prose is enough.

However, Claude Code must justify every recommendation.

## Evaluation criteria for each visual

For each current or proposed visual, Claude Code should evaluate:

1. Does it help the jury understand the project faster?
2. Does it support the main narrative?
3. Does it prove engineering maturity?
4. Does it clarify architecture, implementation, or validation?
5. Is it essential in a 50–70 page report?
6. Could it be merged with another visual?
7. Should it be in the main report or appendix?
8. What tool should be used to create it?
9. What source should it be based on?
10. What caption should it have?

## Current Figure Inventory from v0

These are the current v0 placeholders or planned visuals. They are not final.

### Chapter 1
- Figure 1.1 — Current RFQ process flow at GHI
- Figure 1.2 — Pain points mapped to RFQ lifecycle phases
- Figure 1.3 — Four-pillar target architecture of the platform

### Chapter 2 / Future Chapter 3
- Figure 2.1 — System-level use case diagram
- Figure 2.2 — Activity diagram: Advance RFQ Stage
- Figure 2.3 — Activity diagram: Ask Copilot About an RFQ
- Figure 2.4 — Consolidated sprint timeline

### Chapter 3 / Future Chapter 4
- Figure 3.1 — Global architecture of the platform
- Figure 3.2 — Microservices architecture
- Figure 3.3 — Manager service ERD
- Figure 3.4 — Trust-boundary architecture of the RFQ Copilot
- Figure 3.5 — Evidence boundary diagram
- Figure 3.6 — Platform integration view

### Chapter 4 / Future Chapter 5
- Figure 4.1 — Folder structure of `rfq_manager_ms`
- Figure 4.2 — Turn processing pipeline of `rfq_copilot_ms`
- Figure 4.3 — UI screenshot: RFQ detail view with copilot drawer

## Current Table Inventory from v0

These tables are also open for review.

### Chapter 1
- Table 1.1 — Twelve documented pain points

### Chapter 2 / Future Chapter 3
- Stakeholder alignment matrix
- Functional requirements tables
- Non-functional requirements table
- Product backlog tables
- Traceability matrix

### Chapter 3 / Future Chapter 4
- Scope status of four pillars
- Eight trust boundaries
- Architectural decision register summary

### Chapter 4 / Future Chapter 5
- Principal technologies table

### Chapter 5 / Future Chapter 6
- Validation summary table
- Manager validation evidence table
- Copilot test suite breakdown
- Integration validation status table
- Business impact mapping table

## New visuals needed for the State of the Art chapter

The current v0 does not contain a State of the Art chapter.

Claude Code should propose the best visuals for that chapter, possibly including:

- comparison table of ERP / CPQ / RFQ tools / BI tools / generic LLM assistants / Itqan;
- diagram showing evolution from traditional RFQ process to AI-enabled lifecycle intelligence;
- comparison diagram between naive RAG, generic LLM agent, and trust-bound copilot;
- table of technological concepts: LLM, RAG, agentic system, evidence grounding, microservices, BI;
- positioning matrix showing Itqan’s uniqueness.

Claude Code should decide what is essential and what would overload the chapter.

## Expected output from Claude Code

Claude Code should produce a visual strategy table with:

| Chapter | Visual/Table | Keep / Merge / Delete / Add / Appendix | Priority | Recommended Tool | Source | Reason |

Then it should provide:

1. Essential visuals for v1.
2. Optional visuals.
3. Visuals to move to appendix.
4. Visuals to delete.
5. New visuals for the State of the Art chapter.
6. First 3 visuals to generate.
7. Recommended visual style for the whole report.
8. Warnings about visual overload.

## Final visual principle

The final report should not look like a text dump.

It should look like an engineering report with a clear visual story:

problem → existing approaches → proposed architecture → implementation → validation → impact.

Every visual must earn its place.