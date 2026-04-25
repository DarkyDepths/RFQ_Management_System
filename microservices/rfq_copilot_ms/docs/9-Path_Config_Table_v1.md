# Path Config Table v1.1

**Status:** **draft v1.1** — paper-walkthrough validated, awaiting post-code stress test (phase B). The "frozen v1.0" label is reserved for after phase B passes.
**Date:** 2026-04-25
**Companion:** [rfq_copilot_architecture_v3.html](rfq_copilot_architecture_v3.html) · [10-Stress_Test_Set_v1.md](10-Stress_Test_Set_v1.md)
**Philosophy basis:** [1-COPILOT_PHILOSOPHY.md](1-COPILOT_PHILOSOPHY.md) through [8-Challenges_(Known__Hidden).md](<8-Challenges_(Known__Hidden).md>)

This document is the canonical contract that every turn of the copilot must respect. It defines:
- 9 global invariants
- 7 guardrails, 3 pipeline gates
- 2 trigger glossaries (judge, escalation)
- 13 paths (8 main + 5 protected sub-cases)
- 18 fields per path
- 3 Path Planner extra behaviors

Every Pydantic model, registry, and runtime check in `rfq_copilot_ms` must derive from this table. If implementation disagrees with this document, the document wins until updated.

## Changelog

### v1.1 — 2026-04-25 — Paper-walkthrough corrections

Phase A stress test (30 queries in `10-Stress_Test_Set_v1.md`) surfaced 7 spec gaps. Each was corrected in v1.1:

| ID | Type | Resolution |
|---|---|---|
| **F1** | Convention missing | Deterministic temporal filter set added to §3 (`today`, `this_week`, `overdue`, `due_soon`, `last_quarter`, etc.). Anything else falls back to tiny-LLM. |
| **F2** | Policy clarification | Path 7 — confirmed reject-all on `group_C_field_requested`; partial Group A is NOT answered separately. v2 may add multi-intent splitting. |
| **F3** | Model selection rule | Path 3 — Haiku 4.5 for flat listings; Sonnet 4.6 when synthesis keywords present (`summarize`, `patterns`, `trends`, `top by metric`). |
| **F4** | Trigger added | New ESCALATION_TRIGGER `multi_intent_cross_path_detected`. Paths 4 and 5 escalation maps escalate to 8.3 with clarification. |
| **F5** | Family 7 handling | New §2.6 documents Planner re-classification on `pending_clarification` reads. Family 7 is a Planner behavior, not a Path. |
| **F6** | Trigger added | New ESCALATION_TRIGGER `concept_with_rfq_reference_in_same_turn`. Path 2 escalates to 8.3 with "explain or apply?" template. |
| **F7** | Behavior documented | New §2.6 documents stale-conversation handling: fresh thread spawn + system finalizer prepend before classification. |

This is a pre-code spec. Phase B (post-code) will produce v1.2 corrections (likely a different set of findings) before "frozen v1.0".

---

## 1. Nine global invariants

These apply to every turn, regardless of path.

| ID | Invariant |
|---|---|
| **I1** | **Context packet rule** — only the fields requested by the current turn are injected into the prompt. Pre-fetched data may live in session cache, but raw payloads are never passed to the LLM. |
| **I2** | **Resolver vs Evidence separation** — Resolver tools execute deterministically before the agent and are never exposed in L4 (Tool descriptions). |
| **I3** | **Access ordering** — Access policy runs before any Evidence tool call. A denied access produces an immediate Escalation, never a tool result. |
| **I4** | **Existence-leak policy** — default mode allows distinct messages for "missing" vs "inaccessible" (single and multi-target). Strict mode (config toggle) renders both as a uniform "could not ground" message. |
| **I5** | **Escalation inheritance** — when a path is entered via Escalation Gate, the destination inherits the caller's resolved target, access verdict, retrieved evidence, and working memory. The destination does not re-run target resolution or access checks. |
| **I6** | **Access ≠ Evidence** — Access policy is owned by `rfq_manager_ms` for every path that targets an RFQ, regardless of which service holds the evidence. Intelligence and any future service trust manager-validated access. |
| **I7** | **Cross-target context isolation (Path 7)** — each target's evidence packet is built independently and labelled per target. No field from target A's packet may answer about target B. The Judge verifies each claim's grounding label. |
| **I8** | **Cross-context memory fan-out (Path 6)** — working memory always belongs to the thread owner; episodic memory loaded for a turn belongs to the current target (which may differ from the owner). Context Packet Builder labels each evidence field with its `target_id`. |
| **I9** | **Aggregate-count leak prohibition** — counts, sums, or sizes of inaccessible items MUST NOT be exposed (Paths 3 and 7 in particular). Sanity filtering is internal; visible counts are accessibility-bounded only. |

---

## 2. Glossary

### 2.1 Pipeline gates (3 named components)

| Component | Role |
|---|---|
| **Path Planner** | First stage. Deterministic classifier (regex, signals, state) with tiny-LLM fallback when uncertain. Emits `TurnExecutionPlan` which declares which stages are active for this turn. |
| **Evidence Check** | Deterministic gate between Agent tool call and Agent compose. Empty / 404 / 0-passages → escalates before composition. The LLM never composes against missing evidence. |
| **Escalation Gate** | Single intercept point for all stage failures. Consumes ESCALATION_TRIGGERS, applies I5 inheritance, routes to a Path 8.x sub-case. Stage failures never loop back to the Planner. |

### 2.2 Guardrails (7)

| Guardrail | Role |
|---|---|
| `scope` | Off-domain content blocked; redirect with one-line decline. |
| `evidence` | Every factual claim must have a `source_ref`. Unreferenced claims are stripped; gap stated honestly. |
| `shape` | Response length / format within bounds for the path. |
| `access` | Pre-retrieval permission check. Owns the I3 ordering. |
| `ambiguity_loop_check` | Never asks the same clarification twice. After two unresolved rounds → escalate to 8.5. |
| `comparable_field_policy` | Path 7 only. Filters requested fields into Group A / B / C; Group C is rejected before retrieval. |
| `target_isolation` | Paths 6 and 7. Prevents fields from one target leaking into a claim about another. |

### 2.3 JUDGE_TRIGGERS

Post-compose triggers that evaluate the draft answer.

| Trigger | Meaning |
|---|---|
| `answer_makes_factual_claim` | Draft asserts a specific fact (deadline, owner, status, etc.). |
| `answer_mentions_other_rfq` | Draft references an RFQ different from the conversation owner. |
| `answer_uses_manager_evidence` | Draft cites operational data. |
| `answer_uses_intelligence_artifact` | Draft cites briefing / snapshot / workbook content. |
| `answer_contains_comparison` | Draft puts two or more targets side-by-side. |
| `answer_contains_recommendation_or_judgment` | Draft offers a "should" / "better" / "recommended" statement. |
| `answer_mentions_missing_data` | Draft acknowledges a known gap explicitly. |
| `answer_contains_out_of_scope_content` | Draft drifts outside RFQ / industrial domain. |
| `answer_makes_forbidden_inference` | Path 5. Draft infers readiness, risk, gaps, compliance, or workbook conclusions without explicit artifact support. |

### 2.4 ESCALATION_TRIGGERS

Pre / mid-pipeline triggers that change the active path.

| Trigger | Meaning |
|---|---|
| `target_resolution_failed` | RFQ identifier not found. |
| `access_denied` | RFQ exists but user lacks access. |
| `ambiguous_target` | 0 or N candidates from search; reference unclear. |
| `artifact_not_found` | Intelligence artifact 404 for an accessible RFQ. |
| `evidence_missing` | Tool result empty / 0-passages. |
| `scope_drift` | Out-of-domain content detected at compose time. |
| `stale_conversation` | Last activity beyond freshness threshold. |
| `user_asks_operational` | Mid-Path 5 redirection toward Path 4. |
| `user_asks_intelligence` | Mid-Path 4 redirection toward Path 5. |
| `user_asks_comparison` | Mid-anywhere redirection toward Path 7. |
| `user_picks_one_from_list` | Mid-Path 3 redirection toward Path 4. |
| `user_pivots_to_specific_rfq` | Mid-Path 2 redirection toward Path 4 or 5. |
| `user_persists_on_cross` | Mid-Path 6, suggests context switch (no auto). |
| `user_asks_judgment_or_ranking` | → 8.1 unsupported. |
| `user_asks_winner_or_better` | Path 7 → 8.1 unsupported. |
| `user_asks_comparison_among_results` | Mid-Path 3 redirection toward Path 7. |
| `concept_outside_bounded_kb` | Path 2 → 8.2 out-of-scope. |
| `rag_returned_zero_passages` | Path 2 → 8.5 (replaces `evidence_missing` for RAG). |
| `protected_norm_access_denied` | Path 2 with internal-norm permission failure. |
| `search_returned_zero` | Path 3 → 8.5. |
| `search_returned_too_many` | Path 3 → 8.3 clarification. |
| `any_target_resolution_failed` | Path 7 with at least one target missing. |
| `all_targets_inaccessible` | Path 7 with no accessible target. |
| `partial_inaccessibility` | Path 7 with mixed accessibility (≥1 OK, ≥1 denied). |
| `ambiguous_target_count_exceeded` | Path 7 with > 5 candidate targets. |
| `group_C_field_requested` | Path 7 with forbidden judgment field. |
| `all_requested_fields_ungrounded` | Path 7 with no Group A or B fields available. |
| `multi_intent_cross_path_detected` | (F4) Single message contains intents that span paths (e.g. ops on a single RFQ + portfolio temporal aggregation). Routes to 8.3 with clarification. |
| `concept_with_rfq_reference_in_same_turn` | (F6) Path 2 detects a domain concept AND an explicit RFQ reference in the same message. Routes to 8.3 with "explain or apply?" template. |

### 2.5 Session state keys

State persisted at session level (beyond per-turn working memory).

| Key | Writer | Reader | Role |
|---|---|---|---|
| `pending_clarification` | Path 8.3 | Family 7 (Clarification response) | Holds original query + N candidates + clarification round counter. Used to resolve next-turn clarification reply. |
| `last_search_results` | Path 3 | Same path on follow-up turn | Enables "show more" / "the 3rd one" / "narrow by client" follow-ups without re-searching. |

### 2.6 Path Planner extra behaviors

Three deterministic behaviors of the Planner that don't fit the per-path config — they happen **before or alongside** classification.

#### 2.6.1 Stale conversation handling (F7)

When `stale_conversation` is detected (last_activity beyond freshness threshold — 3 days for general threads, 7 days for RFQ threads), the Planner:

1. Spawns a fresh thread for the same target (preserving owner identity).
2. Prepends a system finalizer: `"Starting a fresh conversation about {target}."`
3. Then runs normal classification on the actual user message.

The user's stored thread history remains accessible manually but is not auto-loaded into working memory.

#### 2.6.2 Clarification response handling (F5 — Family 7)

When the previous turn left `pending_clarification` in session state AND the current message looks like a resolution reply (short, often a numeric index, an RFQ code, or a deictic descriptor — `"yes, the third one"`, `"IF-0041"`, `"the Aramco one"`), the Planner:

1. Reads `pending_clarification` from session state.
2. Resolves the chosen candidate by index, code, or descriptor matching.
3. Clears `pending_clarification`.
4. Re-classifies the **original** ask into its proper path (typically Path 4, 5, or 7) with the now-resolved target.

If the reply itself is still ambiguous (e.g. matches no candidate, or matches multiple), the Planner stays in 8.3 and asks one more clarification — the `ambiguity_loop_check` guardrail prevents infinite loops (after 2 rounds → 8.5).

Family 7 from `5-Query_Families.md` is therefore implemented as **Planner behavior**, not as a separate Path entry.

#### 2.6.3 Tiered model selection on Path 3 (F3)

The Planner picks the model for Path 3 based on the request's nature:

- **Haiku 4.5** if the request is a flat listing or filter (no synthesis keywords present).
- **Sonnet 4.6** if the request contains any of: `summarize`, `summary`, `synthesize`, `patterns`, `trends`, `top by`, `rank by`, `compare across`, `aggregate`, `breakdown`.

Synthesis-mode also activates the Judge (verdict_only) since aggregate claims are easier to fabricate than line-by-line listings.

---

## 3. Notation conventions

| Convention | Meaning |
|---|---|
| `dynamic: ...` | Cell content depends on the requested field or sub-topic at runtime (e.g. Path 7 Allowed evidence). |
| `[default → END]` | Path is terminal. Finalizer is the exit; no further escalation. |
| **Soft trigger** | Modifies the finalizer template (e.g. staleness caveat). Path stays the same. |
| **Hard trigger** | Changes the active path via Escalation Gate. Never routes back to the Planner. |
| Resolver / Evidence categorization | **Per-path, not per-tool.** The same tool may be a Resolver in one path and an Evidence tool in another (e.g. `search_portfolio` in Path 4 vs Path 3). |
| Evidence Check fail | Always escalates **before** compose. The LLM never composes against missing evidence. |
| **Temporal filter set (F1)** | The Planner recognizes a **deterministic** set of temporal filters and translates them to manager_ms query params: `today`, `tomorrow`, `yesterday`, `this_week`, `next_week`, `last_week`, `this_month`, `next_month`, `last_month`, `this_quarter`, `last_quarter`, `this_year`, `last_year`, `overdue` (deadline < today AND status not terminal), `due_soon` (deadline within next 7 days). Any temporal phrasing outside this set falls back to tiny-LLM fallback in the Planner. |

---

## 4. Path Configurations

Each path declares 18 fields. Fields use the glossary terms defined in Section 2.

The 18 fields, in fixed order:

1. `Path` — id
2. `Intent` — one-line user intention
3. `Applicable entry contexts` — `general` / `RFQ-bound` / `both`
4. `Target shape` — `none` / `concept` / `one_rfq` / `another_rfq` / `many_rfqs` / `pair` / `n_tuple` / `rfq_vs_slice` / `unresolved` / `any` / inherited
5. `Target resolver` — strategy
6. `Resolver tools` — off-agent, deterministic
7. `Access policy` — pre-retrieval enforcement
8. `Allowed evidence` — source(s) of truth permitted
9. `Evidence tools` — agent-exposed tools
10. `Context layers` — subset of L1-L5
11. `Memory policy` — working / episodic / pre-fetch parameters
12. `Guardrails` — ordered list
13. `Judge policy` — `none` / `conditional(<trigger expr>)` / `always`
14. `Model profile` — model + temperature
15. `Token budget` — total in+out, output cap
16. `Escalation map` — ordered rules, first match wins
17. `Finalizer template` — outcome-specific phrasing
18. `Persistence policy` — 7 sub-fields (working_memory, episodic_contribution, store_tool_calls, store_source_refs, update_last_activity, store_judge_verdict, session_state_writes)

---

### Path 1 — Conversational

Greetings, thanks, identity, micro-help. No business data.

| Field | Value |
|---|---|
| Path | 1 |
| Intent | greetings / thanks / identity / micro-help — user is talking to the assistant, not querying business data |
| Applicable entry contexts | both |
| Target shape | none |
| Target resolver | N/A |
| Resolver tools | ∅ |
| Access policy | N/A |
| Allowed evidence | none |
| Evidence tools | ∅ |
| Context layers | L1 (subset persona, ~150 tok) + L5 |
| Memory policy | working: 3 turns ; episodic: none |
| Guardrails | [scope, shape] |
| Judge policy | none |
| Model profile | template-first matcher (registry); Haiku 4.5 fallback for unmatched conversational; temp 0.3 |
| Token budget | ~300 in+out; output ≤ 80 |
| Escalation map | <pre>[<br>  scope_drift                  → 8.2_out_of_scope,<br>  user_pivots_to_specific_rfq  → reclassify (3, 4, 5),<br>  default                      → END<br>]</pre> |
| Finalizer template | scope drift → "I'm here to help with RFQ work — what do you need?" ; otherwise → template registry response |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: none ; store_source_refs: no ; update_last_activity: yes ; store_judge_verdict: none ; session_state_writes: [] |

---

### Path 2 — Domain knowledge

Industrial / RFQ concepts. Bounded RAG only.

| Field | Value |
|---|---|
| Path | 2 |
| Intent | explain industrial / RFQ-domain concept (PWHT, RT, ASME Sec VIII, TEMA, API 660/661, Aramco SAES/SAEP, GHI norms…) |
| Applicable entry contexts | both |
| Target shape | concept |
| Target resolver | N/A |
| Resolver tools | ∅ |
| Access policy | conditional — if concept touches "GHI internal norms" (protected KB), check role; otherwise N/A |
| Allowed evidence | bounded domain KB (Vector DB) — not internet, not manager, not intelligence |
| Evidence tools | `query_rag` |
| Context layers | L1 (persona + few-shot domain) + L3 (RAG passages, top 3) + L4 + L5 (no L2) |
| Memory policy | working: 3 turns ; episodic: none |
| Guardrails | [scope, evidence, shape] — scope CRITICAL to avoid generic-internet drift |
| Judge policy | **tiered** — `none` for short glossary/template ; `conditional` for standards-sensitive content ; `conditional` for multi-passage synthesis ; `mandatory` if applicability or judgment claim |
| Model profile | Haiku 4.5 for simple explanation; Sonnet 4.6 for multi-passage synthesis; temp 0.3 |
| Token budget | ~1500 in+out; output ≤ 400 |
| Escalation map | <pre>[<br>  concept_outside_bounded_kb                 → 8.2_out_of_scope,<br>  rag_returned_zero_passages                 → 8.5_no_evidence (BEFORE compose),<br>  user_pivots_to_specific_rfq                → Path 4 or 5,<br>  protected_norm_access_denied               → 8.4_inaccessible,<br>  concept_with_rfq_reference_in_same_turn    → 8.3 (clarification: "I can explain {concept}, or apply it to {rfq} — which?"),<br>  default                                    → finalizer<br>]</pre> |
| Finalizer template | success → grounded explanation with source_refs ; out_of_kb → "{concept} isn't in my domain knowledge — I focus on RFQ, estimation, and industrial standards." ; partial → "Here's what I have on {concept}: {summary}. Missing: {aspects}." |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: yes (RAG queries + retrieved doc IDs) ; store_source_refs: yes (KB doc refs) ; update_last_activity: yes ; store_judge_verdict: verdict_only when fired ; session_state_writes: [] |

---

### Path 3 — Portfolio retrieval

Search / list / filter many RFQs. Search IS the evidence.

| Field | Value |
|---|---|
| Path | 3 |
| Intent | search / filter / list / summarize multiple RFQs at portfolio level ("urgent RFQs", "Aramco projects", "blocked RFQs", "win rate by client") |
| Applicable entry contexts | both (primary in general) |
| Target shape | many_rfqs / portfolio_slice |
| Target resolver | N/A — Path 3 does not resolve to a single ID; the search itself is the answer |
| Resolver tools | ∅ |
| Access policy | actor-scoped query at source (manager_ms must filter by accessibility) ; copilot performs post-retrieval sanity filter ; counts of inaccessible items MUST NOT be exposed (I9) |
| Allowed evidence | rfq_manager_ms only |
| Evidence tools | `search_portfolio`, `get_dashboard_metrics`, `get_dashboard_analytics` |
| Context layers | L1 + L2 (working only) + L4 + L5 (no L3) |
| Memory policy | working: 6 turns ; episodic: none |
| Guardrails | [evidence, scope, shape, access (post-retrieval sanity)] |
| Judge policy | `conditional(answer_makes_factual_claim AND result_count > 0)` |
| Model profile | **Haiku 4.5** if flat listing/filter (no synthesis keywords); **Sonnet 4.6** if synthesis keywords present (`summarize`, `patterns`, `trends`, `top by`, etc. — see §2.6.3 for the full set); temp 0.2 |
| Temporal filters | Deterministic set per §3 (`today`, `this_week`, `overdue`, `due_soon`, `last_quarter`, etc.). Outside the set → tiny-LLM fallback. |
| Token budget | ~3000 in+out; output ≤ 600 |
| Escalation map | <pre>[<br>  search_returned_zero               → 8.5_no_evidence,<br>  search_returned_too_many (>20)     → 8.3_clarification,<br>  user_picks_one_from_list           → Path 4,<br>  user_asks_judgment_or_ranking      → 8.1_unsupported,<br>  user_asks_comparison_among_results → Path 7,<br>  default                            → finalizer<br>]</pre> |
| Finalizer template | success → structured list (count + key fields per RFQ) — counts reflect accessible RFQs only ; zero → "I couldn't find RFQs matching {filters}." ; too_many → "I see {N} matches — narrow with client / date / status?" |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: yes ; store_source_refs: yes (`manager_ms:/rfqs?{query}@{ts}`) ; update_last_activity: yes ; store_judge_verdict: verdict_only when fired ; session_state_writes: [last_search_results] |

---

### Path 4 — RFQ operational retrieval

One identifiable RFQ. Operational truth from manager_ms.

| Field | Value |
|---|---|
| Path | 4 |
| Intent | get one identifiable RFQ's operational truth (deadline, owner, status, current stage, blocker, priority, progress, reminders summary) |
| Applicable entry contexts | RFQ-bound (primary) + general if RFQ named explicitly |
| Target shape | one_rfq |
| Target resolver | (a) RFQ-bound, no explicit ref → page_default_rfq_id ; (b) explicit ref → `search_portfolio` deterministic 0/1/N branch ; (c) ambiguous descriptor → idem |
| Resolver tools | `search_portfolio` (manager_ms) — off-agent only |
| Access policy | pre-retrieval check via manager_ms `/rfqs/{id}` with actor headers ; 403/404 → escalate 8.4 ; audit logged |
| Allowed evidence | rfq_manager_ms only |
| Evidence tools | `get_rfq_profile`, `get_rfq_stages`, `list_reminders(rfq_id)` |
| Context layers | L1 (persona + few-shot ops) + L2 (working + episodic scoped to rfq_id + pre-fetched profile/stages if RFQ-bound) + L4 (3 tools) + L5 — no L3 |
| Memory policy | working: 6 turns ; episodic: filtered by rfq_id ; pre-fetched profile/stages reused if loaded at session open ; re-fetch if stale |
| Guardrails | [access, evidence, scope, shape] — access first |
| Judge policy | `conditional(answer_makes_factual_claim)` ; deterministic claim detector ; skipped for ack/confirmation |
| Model profile | Sonnet 4.6 ; temp 0.2 |
| Token budget | ~3000 in+out; output ≤ 400 |
| Escalation map | <pre>[<br>  target_resolution_failed         → 8.4_missing,<br>  access_denied                    → 8.4_inaccessible,<br>  ambiguous_target                 → 8.3,<br>  evidence_missing                 → 8.5_no_evidence (from Evidence Check),<br>  user_asks_intelligence           → Path 5,<br>  user_asks_comparison             → Path 7,<br>  multi_intent_cross_path_detected → 8.3 (clarification: "do you mean current or historical?"),<br>  default                          → finalizer<br>]</pre> |
| Finalizer template | (1) success → focused answer on one RFQ with source_refs ; (2) ambiguous target → "Which RFQ? I see {N matches}" ; (3) missing → "I could not find {ref} in the platform" ; (4) inaccessible → "You do not have access to that RFQ" ; (5) partial data → "{known fields}; {missing fields} not available" |
| Persistence policy | working_memory: yes ; episodic_contribution: summarized (per rfq_id) ; store_tool_calls: yes ; store_source_refs: yes (`manager_ms:/rfqs/{id}@{ts}`) ; update_last_activity: yes ; store_judge_verdict: verdict_with_reason ; session_state_writes: [] |

---

### Path 5 — RFQ intelligence retrieval

One RFQ. Derived intelligence from intelligence_ms.

| Field | Value |
|---|---|
| Path | 5 |
| Intent | get one RFQ's derived intelligence (briefing, snapshot, gaps, readiness, workbook profile/review, parser status, artifact health) |
| Applicable entry contexts | RFQ-bound (primary) + general if RFQ named explicitly |
| Target shape | one_rfq |
| Target resolver | same as Path 4 |
| Resolver tools | `search_portfolio` (manager_ms) |
| Access policy | pre-retrieval check via **manager_ms** (intelligence_ms has no auth — see I6) ; 403/404 → 8.4 ; audit obligatory |
| Allowed evidence | rfq_intelligence_ms only |
| Evidence tools | `get_rfq_snapshot`, `get_briefing`, `get_workbook_profile`, `get_workbook_review`, `get_artifacts_catalog`, `get_artifact_metadata` |
| Context layers | L1 (persona + few-shot intel) + L2 (working + episodic per rfq_id + cached snapshot/briefing if pre-loaded, fields-filtered) + L4 (5+ tools) + L5 — no L3 |
| Memory policy | working: 6 turns ; episodic: filtered by rfq_id ; pre-fetched snapshot/briefing reused ; **re-fetch if `manager.rfq.updated_at > intelligence.artifact.updated_at` OR TTL exceeded** |
| Guardrails | [access, evidence, scope, shape] |
| Judge policy | `conditional(answer_makes_factual_claim OR answer_uses_intelligence_artifact OR answer_contains_recommendation_or_judgment OR answer_makes_forbidden_inference)` — almost always ON on substantive turns |
| Model profile | Sonnet 4.6 ; temp 0.2 |
| Token budget | ~3500 in+out; output ≤ 500 |
| Escalation map | <pre>[<br>  target_resolution_failed         → 8.4_missing,<br>  access_denied                    → 8.4_inaccessible,<br>  ambiguous_target                 → 8.3,<br>  artifact_not_found               → 8.5_no_evidence (from Evidence Check),<br>  user_asks_operational            → Path 4,<br>  user_asks_comparison             → Path 7,<br>  multi_intent_cross_path_detected → 8.3 (clarification: "do you mean a single-RFQ briefing or a cross-portfolio analysis?"),<br>  default                          → finalizer<br>]</pre> |
| Finalizer template | (1) artifact_not_found → "There's no {artifact_type} artifact for this RFQ yet." ; (2) partial → "{available content}. Some sections are placeholder / cold-start / unavailable: {list}." ; (3) **soft trigger: stale** → "{content}. Note: this snapshot is older than the latest RFQ update — some details may be outdated." ; (4) parser_failed (workbook) → "The workbook parser failed for this RFQ. {parser_report_summary if available}." |
| Persistence policy | working_memory: yes ; episodic_contribution: summarized (intelligence facts per rfq_id) ; store_tool_calls: yes (artifacts queried, 404s, staleness flags) ; store_source_refs: yes (`intelligence_ms:/rfqs/{id}/{artifact}@{retrieved_at}`) ; update_last_activity: yes ; store_judge_verdict: verdict_with_reason ; session_state_writes: [] |

#### Path 5 — Forbidden inferences (visible spec)

The Judge MUST flag any of the following as fabrication via `answer_makes_forbidden_inference`. On detection → escalate to `8.5_no_evidence`.

- readiness conclusion (no readiness artifact present)
- risk score / risk judgment
- gap analysis not present in artifact
- compliance assessment
- workbook conclusion when parser failed or absent
- "is this ready?" judgment

The copilot MAY surface and explain artifacts that exist. It MAY NOT generate these inferences itself.

---

### Path 6 — Cross-RFQ reference

User in thread A explicitly references RFQ B for one question. Conversation ownership stays with A.

| Field | Value |
|---|---|
| Path | 6 |
| Intent | user inside an RFQ thread (or with an RFQ already anchored) explicitly references **another** RFQ for this question only — without changing thread ownership |
| Applicable entry contexts | both (most natural in RFQ-bound) |
| Target shape | another_rfq (1 explicit, distinct from default) |
| Target resolver | explicit reference required → `search_portfolio` deterministic 0/1/N. Vague reference ("the other one") → 8.3 |
| Resolver tools | `search_portfolio` (manager_ms) |
| Access policy | pre-retrieval check on the **cross-target only** (thread owner already verified) ; audit obligatory |
| Allowed evidence | inherited from sub-topic — operational → manager_ms (Path 4 rules) ; intelligence → intelligence_ms (Path 5 rules) |
| Evidence tools | conditional union of Path 4 + Path 5 evidence tools, filtered by sub-topic |
| Context layers | L1 (persona) + L2 (**working memory from owner thread** + episodic from cross-target + on-demand fetched cross-target data) + L4 + L5 |
| Memory policy | working: 6 turns of owner thread ; episodic: load **from cross-target only** ; no automatic pre-fetch for cross — fetch on demand |
| Guardrails | [access (cross-target), evidence, scope, shape, **target_isolation**] |
| Judge policy | `conditional(answer_makes_factual_claim OR answer_uses_intelligence_artifact OR answer_mentions_other_rfq)` |
| Model profile | Sonnet 4.6 ; temp 0.2 |
| Token budget | ~3500 in+out; output ≤ 500 |
| Escalation map | <pre>[<br>  target_resolution_failed → 8.4 (inline, NO thread switch),<br>  access_denied            → 8.4 (inline, NO thread switch),<br>  ambiguous_target         → 8.3,<br>  user_asks_comparison     → Path 7 (suggest, no auto),<br>  user_persists_on_cross   → suggest "switch context?" (no auto),<br>  default                  → finalizer<br>]</pre> |
| Finalizer template | (1) success → cross answer with explicit framing "On {cross}: {answer}." ; (2) missing → "I could not find {ref} in the platform." (thread unchanged) ; (3) inaccessible → "You do not have access to {ref}." (thread unchanged) ; (4) comparison detected → "Sounds like you want to compare — run a comparison between {default} and {cross}?" |
| Persistence policy | working_memory: yes (owner thread) ; episodic_contribution: **NOT to owner**; MAY contribute to cross-target episodic with marker "referenced from {owner_thread}" ; store_tool_calls: yes ; store_source_refs: yes (labelled on cross-target only) ; update_last_activity: yes (owner thread) ; store_judge_verdict: verdict_with_reason ; session_state_writes: [] |

---

### Path 7 — Comparison

2+ RFQs side-by-side. Mandatory judge. Cross-target isolation enforced.

| Field | Value |
|---|---|
| Path | 7 |
| Intent | compare 2+ RFQs (or 1 RFQ vs portfolio_slice) on explicitly comparable dimensions — operational and/or intelligence |
| Applicable entry contexts | both |
| Target shape | pair (2 RFQs) / n_tuple (3-5 RFQs) / rfq_vs_slice (1 RFQ + filter) |
| Target resolver | pair explicit → resolve each ID deterministically ; "compare this with X" in RFQ-bound → A = page_default, B via search_portfolio ; n_tuple → resolve each individually ; rfq_vs_slice → A explicit, slice via `search_portfolio(filters)` ; **cap N ≤ 5** otherwise → 8.3 |
| Resolver tools | `search_portfolio` (manager_ms) |
| Access policy | **per-target check pre-retrieval** ; (a) all accessible → proceed ; (b) ≥1 inaccessible among N≥2 → mixed_access finalizer ; (c) all denied → 8.4 ; (d) rfq_vs_slice → filter slice to accessible_only ; **counts of excluded MUST NOT be exposed (I9)** ; audit per inaccessible |
| Allowed evidence | **dynamic** — `Group A field requested → manager_ms` ; `Group B field requested → intelligence_ms` ; `Group C field requested → REJECT (8.1)` |
| Evidence tools | manager: `get_rfq_profile`, `get_rfq_stages`, `list_reminders` ; intelligence: `get_rfq_snapshot`, `get_briefing`, `get_workbook_profile`, `get_workbook_review`, `get_artifacts_catalog`, `get_artifact_metadata`. Selected per Comparable Field Policy filtering. |
| Context layers | L1 (persona + few-shot comparison) + L2 (working + episodic per target_id) + L4 (filtered tools) + L5 — no L3 |
| Memory policy | working: 6 turns ; episodic: load per target_id ; pre-fetched data reused per target ; **isolation rule**: no cross-injection (target_A's snapshot must not appear in target_B's evidence packet) |
| Guardrails | [access_per_target, comparable_field_policy, evidence, scope, shape, target_isolation] |
| Judge policy | **always** — mandatory per philosophy freeze ; evaluates `answer_makes_factual_claim`, `answer_uses_intelligence_artifact`, `answer_contains_comparison`, `answer_contains_recommendation_or_judgment` |
| Model profile | Sonnet 4.6 default ; **Opus 4.7** if N>3 OR cross-evidence (manager+intelligence) ; temp 0.2 |
| Token budget | ~6000 in+out; output ≤ 800 ; cap N ≤ 5 |
| Escalation map | <pre>[<br>  any_target_resolution_failed     → 8.4_missing,<br>  all_targets_inaccessible         → 8.4_inaccessible,<br>  partial_inaccessibility (N≥2)    → finalizer (mixed_access),<br>  ambiguous_target_count_exceeded  → 8.3,<br>  group_C_field_requested          → 8.1_unsupported,<br>  user_asks_winner_or_better       → 8.1_unsupported,<br>  all_requested_fields_ungrounded  → 8.5_no_evidence,<br>  user_drops_to_single_rfq         → Path 4 or 5,<br>  default                          → finalizer<br>]</pre> |
| Finalizer template | (1) success → table or structured field × target with explicit "missing for {target}" / "not grounded for {target}" markers ; (2) partial → "{grounded comparison}; the following fields aren't grounded for both: {list}" ; (3) mixed_access → "I can't ground a comparison when one of the RFQs is outside your access." (I4 strict mode → "I could not ground the comparison") ; (4) forbidden_judgment → "I don't make 'which is better' calls — here are the grounded fields side by side, your call." ; (5) rfq_vs_slice → "Comparing {default} vs RFQs in the slice." (no excluded count per I9) |
| Persistence policy | working_memory: yes ; episodic_contribution: **summarized PER target_id** (each target receives an entry — fan-out) ; store_tool_calls: yes (audit critical) ; store_source_refs: yes (multiple: target × field × source) ; update_last_activity: yes ; store_judge_verdict: verdict_with_reason ; session_state_writes: [] |

#### F2 clarification — Multi-intent comparison + Group C judgment

When a single message asks for both a comparison (Group A or B fields) AND a forbidden judgment (Group C — `which is better`, `which is more profitable`, win probability, risk score, etc.), v1 rejects **the entire turn** via `group_C_field_requested → 8.1_unsupported`. The Group A or B portion is **NOT** answered separately.

Rationale: separating the answer into "here's the comparison, but I won't say which is better" requires a multi-intent splitter that v1 does not have. The user can re-issue the comparison without the judgment to receive a grounded answer.

v2 may introduce multi-intent splitting if real usage shows this rejection is too coarse.

---

### Path 8 — Protected / non-answerable

Entry from any path via Escalation Gate. Safety net. Five sub-cases.

#### Path 8.1 — Unsupported

| Field | Value |
|---|---|
| Path | 8.1 |
| Intent | ask is in platform domain but capability/feature not built yet |
| Applicable entry contexts | both |
| Target shape | any |
| Target resolver | N/A |
| Resolver tools | ∅ |
| Access policy | N/A |
| Allowed evidence | none |
| Evidence tools | ∅ |
| Context layers | L1 (subset) + L5 |
| Memory policy | working: 3 turns ; episodic: none |
| Guardrails | [shape] |
| Judge policy | none |
| Model profile | template-first; Haiku 4.5 fallback; temp 0.3 |
| Token budget | ~250 in+out; output ≤ 80 |
| Escalation map | `[default → END]` |
| Finalizer template | "I can't do {feature} yet — that's not supported. {short redirect: what I can help with}" |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: none ; store_source_refs: no ; update_last_activity: yes ; store_judge_verdict: none ; session_state_writes: [] |

#### Path 8.2 — Out of scope

| Field | Value |
|---|---|
| Path | 8.2 |
| Intent | ask is outside RFQ / platform / industrial domain |
| Applicable entry contexts | both |
| Target shape | none |
| Target resolver | N/A |
| Resolver tools | ∅ |
| Access policy | N/A |
| Allowed evidence | none |
| Evidence tools | ∅ |
| Context layers | L1 (subset) + L5 |
| Memory policy | working: 3 turns ; episodic: none |
| Guardrails | [shape] |
| Judge policy | none |
| Model profile | template-first; Haiku 4.5 fallback; temp 0.3 |
| Token budget | ~200 in+out; output ≤ 60 |
| Escalation map | `[default → END]` |
| Finalizer template | "That's outside what I help with — I focus on RFQ, estimation, and industrial questions." |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: none ; store_source_refs: no ; update_last_activity: yes ; store_judge_verdict: none ; session_state_writes: [] |

#### Path 8.3 — Ambiguous / needs clarification

| Field | Value |
|---|---|
| Path | 8.3 |
| Intent | question potentially valid but target / intent unresolved |
| Applicable entry contexts | both |
| Target shape | unresolved (0/N candidates, or unclear intent) |
| Target resolver | already attempted upstream — not re-triggered here |
| Resolver tools | ∅ (upstream resolver results passed in) |
| Access policy | N/A (no retrieval until clarification) |
| Allowed evidence | none |
| Evidence tools | ∅ |
| Context layers | L1 + L2 (last 2-3 turns) + L5 |
| Memory policy | working: 3 turns ; episodic: none ; **writes `pending_clarification`** state (original_query + N candidates + clarification_round) |
| Guardrails | [shape, ambiguity_loop_check] |
| Judge policy | none |
| Model profile | template for candidate lists; Haiku for clarification phrasing; temp 0.3 |
| Token budget | ~400 in+out |
| Escalation map | <pre>[<br>  clarification_round ≥ 2 → 8.5_no_evidence,<br>  default                 → finalizer<br>]</pre> |
| Finalizer template | (a) 0 matches → "I couldn't find any RFQ matching {q} — give me an RFQ code or narrow it down?" ; (b) 1 < N ≤ 5 → "I see {N} matches: {list}. Which one?" ; (c) N > 5 → "Several match — narrow with client / date / status?" ; (d) unclear intent → "Did you mean {A} or {B}?" |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: yes (upstream search logged) ; store_source_refs: no ; update_last_activity: yes ; store_judge_verdict: none ; session_state_writes: [pending_clarification] |

#### Path 8.4 — Missing / inaccessible target

| Field | Value |
|---|---|
| Path | 8.4 |
| Intent | explicitly named target does not exist OR user lacks access |
| Applicable entry contexts | both |
| Target shape | one_rfq (the named one) |
| Target resolver | failure already constated upstream (`target_resolution_failed` or `access_denied`) |
| Resolver tools | ∅ (no retry) |
| Access policy | path = consequence of access policy ; the two sub-cases (missing vs inaccessible) produce different messages by default — see I4 |
| Allowed evidence | none — refuse to surface anything about the target |
| Evidence tools | ∅ |
| Context layers | L1 + L5 |
| Memory policy | working: 3 turns ; episodic: **never load** (even if past convo exists) |
| Guardrails | [scope, shape] |
| Judge policy | none |
| Model profile | template-first (deterministic message); no LLM |
| Token budget | ~150 in+out; output ≤ 50 |
| Escalation map | `[default → END]` |
| Finalizer template | (a) missing → "I could not find {ref} in the platform." ; (b) inaccessible → "You do not have access to that RFQ." ; (c) **I4 strict toggle** → both render as "I could not find {ref} in the platform." |
| Persistence policy | working_memory: yes ; episodic_contribution: none ; store_tool_calls: yes (**audit-log mandatory: user_id + attempted_ref + reason**) ; store_source_refs: no ; update_last_activity: yes ; store_judge_verdict: none ; session_state_writes: [] |

#### Path 8.5 — Not enough evidence

| Field | Value |
|---|---|
| Path | 8.5 |
| Intent | in-scope, target valid, but available evidence is insufficient to answer safely |
| Applicable entry contexts | both |
| Target shape | inherited (typically one_rfq or comparison) |
| Target resolver | already done upstream |
| Resolver tools | ∅ |
| Access policy | target is accessible (otherwise 8.4) |
| Allowed evidence | **inherited** — only what was already retrieved by the calling path |
| Evidence tools | ∅ (no fresh retrieval — this path is a finalization) |
| Context layers | L1 + L2 (upstream-retrieved) + L5 |
| Memory policy | working inherited ; no fresh load |
| Guardrails | [evidence, scope, shape] |
| Judge policy | `conditional(answer_makes_factual_claim)` — even when stating gaps, ensure no claim slips without source |
| Model profile | Sonnet 4.6 (producing careful "honest gap" message); temp 0.2 |
| Token budget | ~1500 in+out |
| Escalation map | `[default → END]` |
| Finalizer template | (a) "I have {known_fields_with_values} for {target}. I don't have grounded data for {missing_aspects} right now." ; (b) judgment-forbidden → "{aspect} isn't supported by available artifacts." ; (c) partial comparison → "{partial_comparison}; the rest isn't grounded for both targets." |
| Persistence policy | working_memory: yes ; episodic_contribution: summarized ; store_tool_calls: yes (the upstream retrievals) ; store_source_refs: yes (on the partial known data) ; update_last_activity: yes ; store_judge_verdict: verdict_with_reason ; session_state_writes: [] |

---

## 5. Implementation pointers

When this document is translated into code (Pydantic + registry), the following structure is expected:

- `enum PathId` covers `1, 2, 3, 4, 5, 6, 7, 8_1, 8_2, 8_3, 8_4, 8_5` (13 values)
- `PathConfig` (Pydantic model) holds the 18 fields from this document
- `PATH_CONFIGS: dict[PathId, PathConfig]` is the single registry
- `TurnExecutionPlan` is emitted by Path Planner and references a `PathId`
- `EscalationGate` consumes `EscalationTrigger` enum values and uses each path's `escalation_map`
- `FinalizerTemplate` is its own component, keyed by (PathId, outcome) tuple
- Triggers (judge, escalation) are enum types; their detector implementations are separate modules
- The 9 invariants (I1-I9) are enforced by code, not by prompt — invariants violated by the LLM must be caught by guardrails or the judge

Step 2 of the build plan (Pydantic translation) MUST follow Step 3 (stress test with concrete queries), so the registry is frozen against validated semantics — not against guesses.

---

## 6. Companion artifacts

| File | Role |
|---|---|
| `1-COPILOT_PHILOSOPHY.md` | Founding principle — LLM interprets, system controls |
| `2-The_Platform_Experience.md` | UX behaviour |
| `3-The_big_scenarios.md` | Entry / resume scenarios |
| `4-Capability__Evidence_Boundary_(...)md` | What the system is allowed to claim |
| `5-Query_Families_(...)md` | The 8 query families |
| `6-Query_Families__Capability__Evidence_decision_table.md` | Family × evidence × judge mapping |
| `7-Still_Open.md` | 8 open conception questions (pre-architecture) |
| `8-Challenges_(Known__Hidden).md` | Hidden architectural risks |
| **`9-Path_Config_Table_v1.md` (this file)** | **Frozen execution contract** |
| `rfq_copilot_architecture_v3.html` | Visual architecture (1 canonical pipeline + 8 path traces + reference) |

---

*End of Path Config Table v1.*
