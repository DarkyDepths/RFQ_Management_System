# Bibliography Entries v1 — PFE Report (draft `\bibitem{}` entries)

**Status:** Phase γ draft. 17 `\bibitem{}` entries derived from the verified citation map (`citation_map_v1.md`). Ready for copy into the v1 LaTeX bibliography file (`chapter/XX-Bibliography.tex` or the v1 equivalent) when explicitly authorized.
**Created:** 2026-05-10
**Format:** `\bibitem{}` entries compatible with the v0 report's `thebibliography` environment. Style consistent with engineering-report conventions (IEEE-adjacent), with arXiv IDs preserved, DOIs included where verified, retrieval dates noted for vendor docs, and edition designations explicit for standards bodies.

---

## Books and online articles (5 entries; 1 optional)

```latex
\bibitem{cockburn2005hexagonal}
A. Cockburn, ``Hexagonal Architecture,'' HaT Technical Report, 2005.
Available: \url{https://alistair.cockburn.us/hexagonal-architecture/}
(retrieved 2026-05-10; see Wayback Machine archive for stability).

\bibitem{newman2021microservices}
S. Newman, \emph{Building Microservices: Designing Fine-Grained Systems},
2nd ed. Sebastopol, CA, USA: O'Reilly Media, August 2021.
ISBN: 978-1-492-03402-5.

\bibitem{martin2017cleanarch}
R. C. Martin, \emph{Clean Architecture: A Craftsman's Guide to Software Structure
and Design}. Boston, MA, USA: Prentice Hall, 2017. ISBN: 978-0-13-449416-6.

\bibitem{evans2003ddd}
E. Evans, \emph{Domain-Driven Design: Tackling Complexity in the Heart of
Software}. Boston, MA, USA: Addison-Wesley Professional, August 2003.
ISBN: 978-0-321-12521-7.

\bibitem{dumas2018bpm}
M. Dumas, M. La Rosa, J. Mendling, and H. A. Reijers, \emph{Fundamentals of
Business Process Management}, 2nd ed. Berlin, Germany: Springer, 2018.
ISBN: 978-3-662-56508-7. DOI: \url{https://doi.org/10.1007/978-3-662-56509-4}.
```

## Academic papers (6 entries)

```latex
\bibitem{lewis2020rag}
P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. K\"uttler,
M. Lewis, W.-t. Yih, T. Rockt\"aschel, S. Riedel, and D. Kiela,
``Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,''
in \emph{Advances in Neural Information Processing Systems (NeurIPS)}, vol.~33,
2020. arXiv:2005.11401.

\bibitem{yao2023react}
S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao,
``ReAct: Synergizing Reasoning and Acting in Language Models,''
in \emph{Proc. International Conference on Learning Representations (ICLR)},
2023. arXiv:2210.03629.

\bibitem{brown2020gpt3}
T. B. Brown, B. Mann, N. Ryder, M. Subbiah, J. Kaplan, P. Dhariwal,
A. Neelakantan, P. Shyam, G. Sastry, A. Askell, S. Agarwal, A. Herbert-Voss,
G. Krueger, T. Henighan, R. Child, A. Ramesh, D. M. Ziegler, J. Wu, C. Winter,
C. Hesse, M. Chen, E. Sigler, M. Litwin, S. Gray, B. Chess, J. Clark, C. Berner,
S. McCandlish, A. Radford, I. Sutskever, and D. Amodei,
``Language Models are Few-Shot Learners,''
in \emph{Advances in Neural Information Processing Systems (NeurIPS)}, vol.~33,
2020. arXiv:2005.14165.

\bibitem{ji2023hallucination}
Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. Bang, D. Chen,
W. Dai, H. S. Chan, A. Madotto, and P. Fung,
``Survey of Hallucination in Natural Language Generation,''
\emph{ACM Computing Surveys}, 2023.
DOI: \url{https://doi.org/10.1145/3571730}. arXiv:2202.03629.
% TODO: verify exact ACM CSUR publication year (may be 2022); rename key to
% ji2022hallucination if year is 2022.

\bibitem{bai2022constitutional}
Y. Bai, S. Kadavath, S. Kundu, A. Askell, J. Kernion, A. Jones, A. Chen,
A. Goldie, A. Mirhoseini, C. McKinnon, C. Chen, C. Olsson, C. Olah,
D. Hernandez, D. Drain, D. Ganguli, D. Li, E. Tran-Johnson, E. Perez, J. Kerr,
J. Mueller, J. Ladish, J. Landau, K. Ndousse, K. Lukosuite, L. Lovitt,
M. Sellitto, N. Elhage, N. Schiefer, N. Mercado, N. DasSarma, R. Lasenby,
R. Larson, S. Ringer, S. Johnston, S. Kravec, S. El Showk, S. Fort, T. Lanham,
T. Telleen-Lawton, T. Conerly, T. Henighan, T. Hume, S. R. Bowman,
Z. Hatfield-Dodds, B. Mann, D. Amodei, N. Joseph, S. McCandlish, T. Brown,
and J. Kaplan,
``Constitutional AI: Harmlessness from AI Feedback,''
Anthropic Technical Report, December 2022. arXiv:2212.08073.

\bibitem{zheng2023judge}
L. Zheng, W.-L. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Lin, Z. Li,
D. Li, E. P. Xing, H. Zhang, J. E. Gonzalez, and I. Stoica,
``Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,''
in \emph{Advances in Neural Information Processing Systems (NeurIPS)
Datasets and Benchmarks Track}, vol.~36, 2023. arXiv:2306.05685.
```

## Vendor documentation (4 entries)

```latex
\bibitem{anthropic_tool_use_docs}
Anthropic, ``Tool use with Claude,'' Claude API documentation, retrieved
2026-05-10. Available:
\url{https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/overview}.
% TODO: capture Wayback Machine archive snapshot for stability.

\bibitem{anthropic_structured_outputs_docs}
Anthropic, ``Structured outputs,'' Claude API documentation, retrieved
2026-05-10. Available:
\url{https://platform.claude.com/docs/en/docs/build-with-claude/structured-outputs}.
% TODO: capture Wayback Machine archive snapshot for stability.

\bibitem{sap_cpq_product}
SAP SE, ``SAP CPQ --- Configure, Price, Quote (CPQ) Solutions for Sales,''
SAP product documentation, retrieved 2026-05-10. Available:
\url{https://www.sap.com/products/financial-management/cpq.html}.
% TODO: capture Wayback Machine archive snapshot for stability.
% Note: cited as category-existence reference only (per amendment 4); not for
% product comparison.

\bibitem{salesforce_cpq_docs}
Salesforce, ``Salesforce CPQ --- Getting Started,'' Salesforce Help
(Spring~'26 release, Version 66.0), retrieved 2026-05-10. Available:
\url{https://help.salesforce.com/s/articleView?id=sales.cpq_get_started.htm}.
% TODO: capture Wayback Machine archive snapshot for stability.
% Note: cited as category-existence reference only (per amendment 4); not for
% product comparison.
```

## Standards bodies (2 entries)

```latex
\bibitem{asme_bpvc_viii_div1_2025}
American Society of Mechanical Engineers (ASME), \emph{BPVC.VIII.1-2025: Boiler
and Pressure Vessel Code, Section VIII --- Rules for Construction of Pressure
Vessels, Division 1}, 2025 Edition. New York, NY, USA: ASME, 2025.

\bibitem{tema_standards_11ed}
Tubular Exchanger Manufacturers Association (TEMA), \emph{Standards of the
Tubular Exchanger Manufacturers Association}, 11th Edition. Tarrytown, NY, USA:
Tubular Exchanger Manufacturers Association, Inc.
% TODO: confirm exact publication year of the 11th edition before final
% submission; update key to tema_standards_<year>_11ed if needed.
```

---

## Note on optional entries

### `evans2003ddd`

This entry is **conditionally included** based on a Ch 2 §2.3 prose decision the rewriter must make at drafting time:

- **Include if** Ch 2 §2.3 prose explicitly references domain-driven design, the manager service's seven-entity domain model as DDD-influenced, or the BACAB pattern as situated within the DDD/Hexagonal/Clean Architecture lineage that includes Evans.
- **Exclude if** §2.3 prose only references Hexagonal Architecture (Cockburn) and Clean Architecture (Martin) without invoking DDD specifically. In that case, **remove** the `\bibitem{evans2003ddd}` block from the bibliography file. The Ch 2 verified citation count drops to **16**.

**Decision verification:** after Ch 2 v1 prose is written, run `grep -r '\\cite{evans2003ddd}' chapter/` (or the LaTeX-aware equivalent). Zero matches → remove bibliography entry. One or more matches → keep entry.

---

## Final metadata TODOs

These items are flagged for resolution **before final submission**. They do not block use of the bibliography for chapter drafting, but each must be cleared before the bibliography is treated as final.

| TODO ID | Item | Action | Estimated effort |
|---|---|---|---|
| TODO-γ-1 | `ji2023hallucination` ACM CSUR year | Follow DOI `https://doi.org/10.1145/3571730`; confirm exact volume/issue/year. If 2022, rename key throughout. | ~2 minutes |
| TODO-γ-2 | `tema_standards_11ed` publication year | Locate via TEMA / Accuris / BSB Edge product page; update Year field. | ~5–10 minutes |
| TODO-γ-3 | `evans2003ddd` inclusion decision | Grep `\cite{evans2003ddd}` after Ch 2 v1 prose; remove entry if zero matches. | ~1 minute |
| TODO-γ-4 | Wayback Machine archives for vendor docs | Capture snapshots at `https://web.archive.org/save/<url>` for the 4 vendor URLs; add archive URL to `\bibitem{}` entries. | ~5 minutes |
| TODO-γ-5 | Citation-pass closeout | After all chapters drafted, grep `\cite{TODO_*}` across all .tex files; zero matches expected. | ~5 minutes |
| TODO-γ-6 | Bibliography file consolidation | Copy entries above into v1 bibliography file; verify LaTeX compile. Requires explicit authorization. | ~10–15 minutes |

---

## Provenance and verification trail

These bibliography entries derive from the verified citation map at:
`report_handoff/03_strategy_and_rules/citation_map_v1.md`

Every entry corresponds to a row in the Phase β verification table with status `verified`, supporting evidence (URL retrieved, DOI confirmed, edition designation captured) in the Notes column, and a final action of `keep`.

Removed slots (2.2.C analyst report, 2.4.E LLM agents survey) and softened-claim slots (2.6.C document intelligence survey, 2.2.D RFQ workflow academic) are NOT represented in this bibliography file. Their absence is intentional and the prose adjustments needed to honour their fallback decisions are documented in `citation_map_v1.md` under "Prose impact (for the rewriter when drafting Ch 2)".
