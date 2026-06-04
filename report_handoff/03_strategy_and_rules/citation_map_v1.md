# Citation Map v1 — PFE Report (v1 Chapter 2 + cross-chapter)

**Status:** Phase β complete (all 21 candidate slots processed). Ready for use as the canonical citation reference for the Ch 2 SoA chapter draft and any other chapter that needs to cite from this set.
**Created:** 2026-05-10
**Last updated:** 2026-05-10
**Owner:** Mohamed Guidara (project author); citation work executed in collaboration with Claude Code in plan-mode research session.

---

## Purpose

This file is the canonical citation reference for the v1 PFE report. Per amendment 7 of the Ch 2 creation checklist, it is a persistent artifact (not ephemeral context) and supports:
- Ch 2 v1 SoA chapter drafting (primary use)
- Cross-chapter citations (Ch 1 may cite ASME/TEMA standards; Ch 4 may cite BACAB-pattern lineage; Ch 6 may cite hallucination/trust-bounded sources for the limitations / future work discussion)

It pairs with `bibliography_entries_v1.md` (the draft `\bibitem{}` entries derived from this map).

---

## Citation budget posture

- **Target:** 15–22 verified citations for Ch 2 (per Ch 2 creation checklist amendment 1).
- **Result:** **17 verified** (16 if optional `evans2003ddd` is dropped from Ch 2 §2.3 prose).
- **Removed slots:** 2 (Gartner analyst report; LLM agents survey)
- **Softened-claim slots:** 2 (document intelligence survey; RFQ workflow academic paper) — claims grounded in project sources instead

This sits within the 15–22 target. No invented citations. No cite-laundering.

---

## Phase β verification table — consolidated (Batches 1, 2, 3)

### Batch 1 — Low-risk slots (11 verified)

| Slot ID | Candidate source | Source type | Verified citation key | Final action | Notes (proof) |
|---|---|---|---|---|---|
| 2.3.B | Cockburn, "Hexagonal Architecture" (2005) | other (online article) | `cockburn2005hexagonal` | keep | URL `https://alistair.cockburn.us/hexagonal-architecture/` confirmed live by multiple secondary sources (Wikipedia, AWS Prescriptive Guidance, Hexagonal Me, jmgarridopaz.github.io). HaT Technical Report v0.9, September 4, 2005. Direct WebFetch returned "certificate has expired" — server-side TLS issue, not content invalidation. |
| 2.3.A | Newman, *Building Microservices* (2nd ed.) | book | `newman2021microservices` | keep | URL `https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/` confirmed. Sam Newman, O'Reilly Media, August 2021. ISBN: 9781492034018. |
| 2.3.C | Martin, *Clean Architecture* | book | `martin2017cleanarch` | keep | Verified via WebSearch. Robert C. Martin, Prentice Hall, 2017, ISBN 978-0134494166, 432 pages. Confirmations: Amazon, AbeBooks, Porchlight Books, Blackwell's, Google Books. |
| 2.3.D | Evans, *Domain-Driven Design* | book | `evans2003ddd` | keep (**OPTIONAL**) | Verified via WebSearch. Eric Evans, Addison-Wesley Professional, August 20, 2003, ISBN 9780321125217, 560 pages. Confirmations: O'Reilly catalogue, Amazon, Google Books, ACM DL (DOI 10.5555/861502). **Drop if Ch 2 §2.3 prose does not invoke DDD.** |
| 2.2.E | Dumas et al., *Fundamentals of Business Process Management* (2nd ed., 2018) | book | `dumas2018bpm` | keep | Verified via WebSearch. Marlon Dumas, Marcello La Rosa, Jan Mendling, Hajo A. Reijers. Springer, 2nd ed., 2018. Print ISBN: 9783662565087. eBook ISBN: 9783662565094. DOI: 10.1007/978-3-662-56509-4. |
| 2.4.A | Lewis et al., RAG paper | academic paper | `lewis2020rag` | keep | URL `https://arxiv.org/abs/2005.11401` fetched. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks". 12 authors, lead Patrick Lewis. arXiv ID: 2005.11401. v4 (Apr 12, 2021). **Venue confirmed in arXiv comments: NeurIPS 2020.** |
| 2.4.B | Yao et al., ReAct | academic paper | `yao2023react` | keep | URL `https://arxiv.org/abs/2210.03629` fetched. "ReAct: Synergizing Reasoning and Acting in Language Models". 7 authors, lead Shunyu Yao. arXiv ID: 2210.03629. v3 (Mar 10, 2023). **Venue confirmed: ICLR 2023.** |
| 2.4.D | Brown et al., GPT-3 paper | academic paper | `brown2020gpt3` | keep | URL `https://arxiv.org/abs/2005.14165` fetched. "Language Models are Few-Shot Learners". 31 authors, lead Tom B. Brown. arXiv ID: 2005.14165. **Venue confirmed via NeurIPS proceedings**: `https://papers.nips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html` (NeurIPS 2020). |
| 2.5.A | Ji et al., Hallucination Survey | academic paper | `ji2023hallucination` | keep (**year flag**) | URL `https://arxiv.org/abs/2202.03629` fetched. "Survey of Hallucination in Natural Language Generation". 13 authors, lead Ziwei Ji. arXiv ID: 2202.03629. v7 (Jul 14, 2024). **Venue: ACM Computing Surveys, DOI 10.1145/3571730.** Year flag: arXiv comments say "ACM Computing Surveys (2022)" — verify ACM official year before submission; may switch to `ji2022hallucination`. |
| 2.5.B | Bai et al., Constitutional AI | academic paper (technical report) | `bai2022constitutional` | keep | URL `https://arxiv.org/abs/2212.08073` fetched. "Constitutional AI: Harmlessness from AI Feedback". 48 authors, lead Yuntao Bai. Anthropic. arXiv ID: 2212.08073. December 15, 2022. No formal venue (technical report). |
| 2.5.C | Zheng et al., LLM-as-a-Judge | academic paper | `zheng2023judge` | keep | URL `https://arxiv.org/abs/2306.05685` fetched. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena". 13 authors, lead Lianmin Zheng. arXiv ID: 2306.05685. v4 (Dec 24, 2023). **Venue confirmed: NeurIPS 2023 Datasets and Benchmarks Track.** |

### Batch 2 — Vendor docs and standards bodies (6 verified)

| Slot ID | Candidate source | Source type | Verified citation key | Final action | Notes (proof) |
|---|---|---|---|---|---|
| 2.4.C | OpenAI function calling OR Anthropic tool use | vendor documentation | `anthropic_tool_use_docs` | keep (Anthropic chosen) | OpenAI direct fetch returned 403 (blocked to automated fetch). Switched to Anthropic per OR clause. URL fetched 2026-05-10: `https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview` → 301 redirect to `https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/overview`. Page title: "Tool use with Claude". Documents tool-use pattern in the Claude API. |
| 2.5.D | OpenAI structured outputs OR Anthropic JSON mode | vendor documentation | `anthropic_structured_outputs_docs` | keep (Anthropic chosen) | OpenAI direct fetch returned 403. Switched to Anthropic. URL fetched 2026-05-10: `https://docs.anthropic.com/en/docs/build-with-claude/structured-outputs` → 301 redirect to `https://platform.claude.com/docs/en/docs/build-with-claude/structured-outputs`. Page title: "Structured outputs". Documents JSON outputs (`output_config.format`) and Strict tool use (`strict: true`). |
| 2.2.A | SAP CPQ documentation | vendor documentation | `sap_cpq_product` | keep (with fetch caveat) | Direct fetch of `https://www.sap.com/products/financial-management/cpq.html` returned 403 (sap.com blocks automated fetch). Product existence verified via WebSearch on 2026-05-10 with multiple authoritative SAP URLs: product page, help.sap.com docs ("What is SAP CPQ?"), educational page, SOC 1 audit report. **Citation supports only "ERP-embedded CPQ category exists with SAP as exemplar" — NOT product comparison or superiority.** |
| 2.2.B | Salesforce CPQ documentation | vendor documentation | `salesforce_cpq_docs` | keep | Verified via WebSearch on 2026-05-10. Multiple authoritative URLs: help.salesforce.com (Getting Started article), developer.salesforce.com (Developer Guide), trailhead.salesforce.com (training module), resources.docs.salesforce.com (Spring '26 Developer Guide PDF, Version 66.0, last updated November 17, 2025). **Citation supports only "CPQ category exists with Salesforce as exemplar" — NOT product comparison.** |
| 2.6.A | ASME BPVC Section VIII Division 1 | standards body | `asme_bpvc_viii_div1_2025` | keep | URL fetched 2026-05-10: `https://www.asme.org/codes-standards/find-codes-standards/bpvc-viii-1-bpvc-section-viii-rules-construction-pressure-vessels-division-1`. Title: "BPVC Section VIII — Rules for Construction of Pressure Vessels Division 1". **Current edition: 2025 Edition.** Designation: BPVC.VIII.1-2025. Standards body: ASME. |
| 2.6.B | TEMA Standards | standards body | `tema_standards_11ed` | keep (**year flag**) | URL fetched 2026-05-10: `https://www.tema.org/` and `https://tema.org/standards/`. **Current edition: 11th Edition.** Year flag: TEMA page does not display the 11th edition's publication year on the standards page; verify before final submission. |

### Batch 3 — Medium/high-risk slots (0 verified, 4 fallbacks executed)

| Slot ID | Candidate source | Source type | Verified citation key | Final action | Notes (proof) |
|---|---|---|---|---|---|
| 2.2.C | Gartner Magic Quadrant for CPQ | industry analyst report | (none) | **remove** | Search executed 2026-05-10. Gartner MQ for CPQ confirmed to exist (`https://www.gartner.com/en/documents/6102427`); 2025/2026 vendor press releases citing leader placement found (PROS, SAP, Salesforce, Oracle, Infor). Underlying Gartner report is **paid and not directly accessible for verification**. Per Rule 8 (no paid analyst reports without verified details) and amendment 2, **citation removed**. Category existence is covered by 2.2.A, 2.2.B, 2.2.E. |
| 2.4.E | Recent LLM agents/tool-use survey | academic paper | (none) | **remove** | Search executed 2026-05-10. **Five candidate surveys evaluated**: arXiv:2503.16416, arXiv:2507.21504, Qu et al. arXiv:2405.17935, Masterman et al. arXiv:2404.11584, arXiv:2509.18970. **None confirmed published at NeurIPS/ICLR/ACL/EMNLP main track**; all are arXiv preprints; citation counts not verifiable from search snippets. Per quality threshold + time-bounding instruction, **fallback executed: drop slot**. §2.4 prose stands on slots 2.4.A–2.4.D. |
| 2.6.C | Recent document intelligence survey | academic paper | (none) | **soften claim** | Search executed 2026-05-10. Search returned multiple TPAMI/CSUR surveys on adjacent topics but **no dedicated survey on "document intelligence" or "structured information extraction"** in the requested venues within 2020–2025. Per pre-specified fallback, **claim softened**: §2.6 prose grounds the deterministic-parsing-first stance in Ch 1 §1.5 (asymmetric cost of error) and Ch 5 §5.4 (intelligence service parsers). |
| 2.2.D | RFQ workflow / quotation lifecycle academic | academic paper OR book | (none) | **soften claim** | Search executed 2026-05-10. Returned mostly industry/practitioner resources. **One peer-reviewed candidate** (ResearchGate publication 263443991, 2014) but **2014 falls outside the slot's 2015–2025 date range** and the focus is automotive-specific. Per pre-specified fallback, **claim softened**: §2.2 prose grounds the "RFQ lifecycle as distinct problem from price calculation" framing in Ch 1 audit observations + the BPM textbook (slot 2.2.E). |

---

## Verified citation keys (consolidated, alphabetical)

```
anthropic_structured_outputs_docs
anthropic_tool_use_docs
asme_bpvc_viii_div1_2025
bai2022constitutional
brown2020gpt3
cockburn2005hexagonal
dumas2018bpm
evans2003ddd                           (optional — pending Ch 2 §2.3 prose)
ji2023hallucination                    (year flag — verify ACM CSUR year)
lewis2020rag
martin2017cleanarch
newman2021microservices
salesforce_cpq_docs
sap_cpq_product
tema_standards_11ed                    (year flag — verify 11th edition year)
yao2023react
zheng2023judge
```

Total: **17 keys** (16 if `evans2003ddd` is dropped).

---

## Removed and softened slots (record)

### Removed (2)

- **2.2.C** Gartner/Forrester CPQ analyst report — paid report, not directly verifiable; category existence covered by other slots
- **2.4.E** Recent LLM agents/tool-use survey — no peer-reviewed venue verified within criteria; §2.4 prose stands on the 4 family-seminal sources

### Softened (2)

- **2.6.C** Document intelligence survey — claim grounded in Ch 1 §1.5 + Ch 5 §5.4 instead of external citation
- **2.2.D** RFQ workflow academic — claim grounded in Ch 1 audit + BPM textbook (slot 2.2.E) instead

### Prose impact (for the rewriter when drafting Ch 2)

| Section | Adjustment |
|---|---|
| §2.2 (CPQ market presence) | Frame on vendor docs (2.2.A, 2.2.B) + BPM textbook (2.2.E). Do not cite an analyst report. |
| §2.2 (RFQ-as-distinct-problem from CPQ) | Use: *"As observed at GHI during the audit (Ch 1), the RFQ lifecycle is a coordination problem distinct from price calculation, regardless of how mature the price-calculation tooling is. The broader literature on workflow / business process management (Dumas et al., 2018) supports this framing in adjacent terms."* |
| §2.4 (active research area) | Frame the four families (slots 2.4.A–2.4.D) without a survey-of-surveys. Acceptable wording: *"The four families surveyed below are widely discussed in the current LLM literature; this chapter cites the seminal contribution to each family rather than a meta-survey."* |
| §2.6 (deterministic parsing justification) | Use: *"The intelligence service adopts a deterministic-parsing-first stance, justified by the asymmetric cost of error from Ch 1 §1.5 and demonstrated by the parser implementations in Ch 5 §5.4."* No external citation required. |

---

## Pre-submission TODOs

1. **TODO-γ-1 — Verify `ji2023hallucination` exact ACM CSUR publication year.** Follow DOI `https://doi.org/10.1145/3571730`. If 2022, rename key to `ji2022hallucination` throughout bibliography and chapter `\cite{}` invocations.
2. **TODO-γ-2 — Verify `tema_standards_11ed` publication year of the 11th edition.** Locate via TEMA / Accuris / BSB Edge product page. Update Year field in entry; optionally rename key to include year.
3. **TODO-γ-3 — Drop `evans2003ddd` if Ch 2 §2.3 does not invoke DDD.** Grep `\cite{evans2003ddd}` after Ch 2 v1 prose is written; remove bibliography entry if zero matches.
4. **TODO-γ-4 — Capture Wayback Machine archives for vendor docs.** Four URLs: Anthropic tool use, Anthropic structured outputs, SAP CPQ product, Salesforce CPQ help. Use `https://web.archive.org/save/<url>` for each. Add archive URL to `\bibitem{}` entries as backup.
5. **TODO-γ-5 — Citation-pass closeout verification.** After all chapters drafted, grep `\cite{TODO_*}` across all .tex files; zero matches expected. Each `\cite{X}` resolves to a verified `\bibitem{X}`.

---

## Verification posture (carried forward from cross-chapter rule B-1)

No invented citations. Every `\cite{}` in the final report must resolve to a real, verified `\bibitem{}` in the bibliography. Sources verified through this map are cleared for use; no other source may be cited in the v1 report without being added to this map and verified through the same Phase β process.
