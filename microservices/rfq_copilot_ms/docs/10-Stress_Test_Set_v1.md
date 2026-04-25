# Stress Test Set v1

**Status:** phase A (paper walkthrough) complete · phase B (post-code execution) pending
**Date:** 2026-04-25
**Companion:** [9-Path_Config_Table_v1.md](9-Path_Config_Table_v1.md) · [rfq_copilot_architecture_v3.html](rfq_copilot_architecture_v3.html)

This document is the canonical query set for stress-testing `rfq_copilot_ms`. It serves three purposes:

1. **Spec validation** — does every query land cleanly on exactly one path?
2. **Regression test set** — once `PathPlanner`, `EscalationGate`, `EvidenceCheck`, and `Judge` are coded, this set runs in CI to verify behavior matches the spec.
3. **Few-shot source** — ~12 of the 30 queries are flagged for inclusion as few-shot examples in `PathPlanner` (tiny-LLM fallback) and `Judge` system prompts.

The set is composed of 3 pools of 10 queries each:

| Pool | Purpose | Count |
|---|---|---|
| **A — synthetic** | One query per path; total coverage of the 13 paths | 10 |
| **B — realistic** | Phrasings an estimator/manager would actually type | 10 |
| **C — adversarial** | Designed to break the spec; multi-intent, ambiguous, forbidden | 10 |

---

## Phase A — Paper walkthrough results (2026-04-25)

Phase A was a manual simulation against `9-Path_Config_Table_v1` (pre-F1-F7). It surfaced 7 spec gaps:

- **F1** — temporal filters had no deterministic rule
- **F2** — multi-intent comparison + Group C judgment had no defined behavior
- **F3** — Path 3 listing vs synthesis model selection unclear
- **F4** — multi-intent cross-path (Path 4 + Path 3) had no policy
- **F5** — Family 7 (Clarification response) had no Path entry
- **F6** — concept + RFQ in single message had no trigger
- **F7** — `stale_conversation` trigger had no consumer

These were applied as v1.1 corrections to `9-Path_Config_Table_v1.md`. The `expected_*` fields below reflect **post-correction** behavior. The `result_phase_a` field captures the **pre-correction** observation.

Phase B will execute this set against the actual code and compare actual outcomes to `expected_*`.

---

## How to consume this document

The `queries:` block below is valid YAML. To use it:

```python
import yaml
from pathlib import Path

doc = Path("10-Stress_Test_Set_v1.md").read_text()
yaml_block = doc.split("```yaml\n", 1)[1].rsplit("\n```", 1)[0]
data = yaml.safe_load(yaml_block)
for q in data["queries"]:
    actual = run_planner(q["query"], q["entry"])
    assert actual.path == q["expected"]["path"], f"{q['id']} failed"
```

---

## Test set

```yaml
test_set_version: 1
generated: 2026-04-25
companion_spec: 9-Path_Config_Table_v1.md
companion_spec_version: v1.1
total_queries: 30
phase_a_clean_count: 23
phase_a_finding_count: 7
phase_b_status: pending

# Conventions:
#   id              : A1..A10 (synthetic), B1..B10 (realistic), C1..C10 (adversarial)
#   pool            : synthetic | realistic | adversarial
#   entry.context   : general | rfq_bound
#   entry.rfq_id    : null when general
#   expected.path   : final path (e.g. "1", "4", "8.4") AFTER any escalation
#   expected.entry_path : initial path before escalation, if different from final
#   expected.escalations : ordered list of (trigger, to_path) pairs taken
#   expected.tools_called : tools invoked in expected execution
#   expected.judge_fires : whether the judge runs
#   expected.finalizer_outcome : success | clarify | decline_X | template_response | partial
#   use_as_few_shot_for : [PathPlanner, Judge] subset (empty if test-only)
#   result_phase_a  : clean | finding_F<n> (with finding number)
#   tension         : free-text note when the case is borderline

queries:

  # ============================ POOL A — SYNTHETIC ============================

  - id: A1
    pool: synthetic
    query: "hi"
    entry: { context: general, rfq_id: null }
    expected:
      path: "1"
      target_shape: none
      tools_called: []
      judge_fires: false
      finalizer_outcome: template_response
      persistence_writes: [working_memory]
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: null

  - id: A2
    pool: synthetic
    query: "what does PWHT mean?"
    entry: { context: general, rfq_id: null }
    expected:
      path: "2"
      target_shape: concept
      tools_called: [query_rag]
      judge_fires: false  # tier=none for short glossary
      finalizer_outcome: success
      persistence_writes: [working_memory, source_refs]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A3
    pool: synthetic
    query: "show me all RFQs in Cost estimation stage"
    entry: { context: general, rfq_id: null }
    expected:
      path: "3"
      target_shape: many_rfqs
      tools_called: [search_portfolio]
      judge_fires: false
      finalizer_outcome: success
      persistence_writes: [working_memory, last_search_results, source_refs]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A4
    pool: synthetic
    query: "what's the deadline for IF-0002?"
    entry: { context: general, rfq_id: null }
    expected:
      path: "4"
      target_shape: one_rfq
      target_resolver: search_portfolio_by_code
      tools_called: [get_rfq_profile]
      judge_fires: true
      finalizer_outcome: success
      persistence_writes: [working_memory, episodic, source_refs, judge_verdict]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A5
    pool: synthetic
    query: "what does the briefing say?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "5"
      target_shape: one_rfq
      target_resolver: page_default
      tools_called: [get_briefing]
      judge_fires: true
      finalizer_outcome: success
      persistence_writes: [working_memory, episodic, source_refs, judge_verdict]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A6
    pool: synthetic
    query: "and what about IF-0007?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "6"
      target_shape: another_rfq
      target_resolver: search_portfolio_by_code
      cross_target: "IF-0007"
      thread_owner_unchanged: true
      tools_called: [get_rfq_profile]  # depends on sub-question; example here
      judge_fires: true
      finalizer_outcome: success
      persistence_writes: [working_memory_owner, episodic_cross_target, source_refs, judge_verdict]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: "Sub-topic ('what about') is implicit; Planner must default to operational unless context suggests otherwise"

  - id: A7
    pool: synthetic
    query: "compare IF-0002 and IF-0007 on deadline and current stage"
    entry: { context: general, rfq_id: null }
    expected:
      path: "7"
      target_shape: pair
      target_resolver: search_portfolio_by_code_per_target
      comparable_field_groups: [A, A]  # deadline, current_stage both Group A
      tools_called: [get_rfq_profile, get_rfq_stages]
      judge_fires: true  # mandatory on Path 7
      finalizer_outcome: success
      persistence_writes: [working_memory, episodic_per_target, source_refs, judge_verdict]
    use_as_few_shot_for: [PathPlanner, Judge]
    result_phase_a: clean
    tension: null

  - id: A8
    pool: synthetic
    query: "send an email to the client when this RFQ becomes blocked"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "8.1"
      target_shape: any
      tools_called: []
      judge_fires: false
      finalizer_outcome: decline_unsupported
      persistence_writes: [working_memory]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A9
    pool: synthetic
    query: "what's the weather in Riyadh?"
    entry: { context: general, rfq_id: null }
    expected:
      path: "8.2"
      target_shape: none
      tools_called: []
      judge_fires: false
      finalizer_outcome: decline_out_of_scope
      persistence_writes: [working_memory]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: A10
    pool: synthetic
    query: "what's the deadline for IF-9999?"
    entry: { context: general, rfq_id: null }
    setup_assumption: "IF-9999 does not exist in rfq_manager_ms"
    expected:
      entry_path: "4"
      escalations:
        - trigger: target_resolution_failed
          to: "8.4_missing"
      path: "8.4"  # final
      finalizer_outcome: decline_missing_target
      persistence_writes: [working_memory, audit_log]
    use_as_few_shot_for: [PathPlanner, Judge]
    result_phase_a: clean
    tension: null

  # ============================ POOL B — REALISTIC ============================

  - id: B1
    pool: realistic
    query: "any blockers?"
    entry: { context: rfq_bound, rfq_id: "IF-0008" }
    expected:
      path: "4"
      target_resolver: page_default
      tools_called: [get_rfq_profile]
      judge_fires: true
      finalizer_outcome: success
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: B2
    pool: realistic
    query: "who owns this?"
    entry: { context: rfq_bound, rfq_id: "IF-0008" }
    expected:
      path: "4"
      target_resolver: page_default
      tools_called: [get_rfq_profile]
      judge_fires: true
      finalizer_outcome: success
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: null

  - id: B3
    pool: realistic
    query: "is the workbook ready?"
    entry: { context: rfq_bound, rfq_id: "IF-0008" }
    expected:
      path: "5"
      target_resolver: page_default
      tools_called: [get_workbook_profile, get_workbook_review]
      judge_fires: true
      conditional_branch:
        - if: "artifact_contains_explicit_readiness"
          then: { finalizer_outcome: success }
        - else:
            escalations:
              - trigger: answer_makes_forbidden_inference
                to: "8.5_no_evidence"
            path: "8.5"
            finalizer_outcome: decline_no_evidence
    use_as_few_shot_for: [Judge]  # tests Path 5 forbidden block
    result_phase_a: clean
    tension: "'ready' is a judgment word; outcome depends on artifact contents"

  - id: B4
    pool: realistic
    query: "what's the latest Aramco RFQ we have?"
    entry: { context: general, rfq_id: null }
    expected:
      path: "3"
      tools_called: [search_portfolio]  # filters: client=Aramco, sort=created_desc, size=1
      judge_fires: false
      finalizer_outcome: success
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: "may reclassify to Path 4 if user picks the result on next turn"

  - id: B5
    pool: realistic
    query: "show me overdue RFQs"
    entry: { context: general, rfq_id: null }
    expected:
      path: "3"
      tools_called: [search_portfolio]  # filter: temporal=overdue
      temporal_filter_used: overdue  # F1: deterministic recognition
      judge_fires: false
      finalizer_outcome: success
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F1
    tension: "'overdue' must map to deterministic temporal filter; F1 added the rule"

  - id: B6
    pool: realistic
    query: "remind me what stage we're at"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "4"
      target_resolver: page_default
      tools_called: [get_rfq_profile]
      judge_fires: true
      finalizer_outcome: success
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: null

  - id: B7
    pool: realistic
    query: "what's missing for the bid package?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "5"
      tools_called: [get_briefing]  # field: what_is_missing
      judge_fires: true
      finalizer_outcome: success
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: "if briefing.what_is_missing is null/empty → finalizer renders partial template"

  - id: B8
    pool: realistic
    query: "ok, thanks"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "1"
      target_shape: none
      tools_called: []
      judge_fires: false
      finalizer_outcome: template_response
      persistence_writes: [working_memory]
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: "Path 1 applies regardless of context; thread ownership untouched"

  - id: B9
    pool: realistic
    query: "any follow-up needed today?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      path: "4"
      tools_called: [list_reminders]  # filter: rfq_id, due=today
      temporal_filter_used: today
      judge_fires: true
      finalizer_outcome: success
    use_as_few_shot_for: []
    result_phase_a: clean
    tension: null

  - id: B10
    pool: realistic
    query: "find me the SWCC project"
    entry: { context: general, rfq_id: null }
    expected:
      path: "3"
      tools_called: [search_portfolio]
      judge_fires: false
      conditional_branch:
        - if: "exactly_one_match"
          then:
            escalations:
              - trigger: user_picks_one_from_list
                to: "Path_4"
            path: "4"
        - else: { path: "3", finalizer_outcome: success }
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: "1 match auto-promotes; >1 leaves as listing"

  # ============================ POOL C — ADVERSARIAL ============================

  - id: C1
    pool: adversarial
    query: "compare these and tell me which is more profitable"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    setup_assumption: "previous turn was about IF-0002 + IF-0007"
    expected:
      entry_path: "7"
      escalations:
        - trigger: group_C_field_requested  # profitability ∈ Group C
          to: "8.1_unsupported"
      path: "8.1"
      finalizer_outcome: decline_unsupported
      decision_origin: "F2 — reject-all (whole turn declined; partial Group A NOT answered)"
    use_as_few_shot_for: [PathPlanner, Judge]
    result_phase_a: finding_F2
    tension: "user might want partial Group A; v1 rejects whole turn (F2 decision)"

  - id: C2
    pool: adversarial
    query: "what about the other one?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    setup_assumption: "no recent listing in working memory; vague reference"
    expected:
      entry_path: "6"
      escalations:
        - trigger: ambiguous_target
          to: "8.3_clarification"
      path: "8.3"
      finalizer_outcome: clarify
      session_state_writes: [pending_clarification]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: null

  - id: C3
    pool: adversarial
    query: "summarize the Aramco portfolio"
    entry: { context: general, rfq_id: null }
    expected:
      path: "3"
      tools_called: [search_portfolio, get_dashboard_metrics]
      synthesis_triggered: true  # F3: 'summarize' keyword → Sonnet, not Haiku
      model_profile: "Sonnet 4.6"
      judge_fires: true  # synthesis warrants judge
      finalizer_outcome: success
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F3
    tension: "F3 disambiguated listing vs synthesis via keyword set"

  - id: C4
    pool: adversarial
    query: "is this RFQ winnable?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      entry_path: "5"
      escalations:
        - trigger: answer_makes_forbidden_inference  # winnability ≈ win probability
          to: "8.5_no_evidence"
      path: "8.5"
      finalizer_outcome: decline_no_evidence
    use_as_few_shot_for: [Judge]
    result_phase_a: clean
    tension: "judge catches forbidden inference at compose stage"

  - id: C5
    pool: adversarial
    query: "how does our blocker compare to last quarter?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    expected:
      entry_path: "4"
      escalations:
        - trigger: multi_intent_cross_path_detected  # F4: ops + portfolio_temporal
          to: "8.3_clarification"
      path: "8.3"
      finalizer_outcome: clarify
      clarification_template: "Do you mean current blocker on IF-0002, or historical blocker patterns last quarter?"
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F4
    tension: "F4 added trigger; v1 rejects with clarification (decision (a))"

  - id: C6
    pool: adversarial
    query: "actually IF-9999, what's its deadline?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    setup_assumption: "IF-9999 does not exist"
    expected:
      entry_path: "6"
      escalations:
        - trigger: target_resolution_failed
          to: "8.4_missing"
      path: "8.4"
      finalizer_outcome: decline_missing_target_inline
      thread_owner_unchanged: true  # remains IF-0002
      persistence_writes: [working_memory_owner, audit_log]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: "Path 6 escapes inline to 8.4 without changing thread ownership"

  - id: C7
    pool: adversarial
    query: "yes, the third one"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    setup_assumption: "previous turn left pending_clarification with N=4 candidates from a search"
    expected:
      planner_behavior: "F5 — read pending_clarification, resolve to candidate index 3, clear state, re-classify into original path"
      original_path: "4"  # whatever the original ask was
      path: "4"  # final after re-classification
      session_state_reads: [pending_clarification]
      session_state_clears: [pending_clarification]
      finalizer_outcome: success
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F5
    tension: "F5 — Family 7 handled by Planner re-classification (decision (b)), not as a separate Path entry"

  - id: C8
    pool: adversarial
    query: "what was that thing about ASME for IF-0008?"
    entry: { context: general, rfq_id: null }
    expected:
      entry_path: "2"
      escalations:
        - trigger: concept_with_rfq_reference_in_same_turn  # F6
          to: "8.3_clarification"
      path: "8.3"
      finalizer_outcome: clarify
      clarification_template: "I can explain ASME, or apply it to IF-0008 — which?"
      session_state_writes: [pending_clarification]
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F6
    tension: "F6 added trigger; same-turn pivot now resolved via clarification"

  - id: C9
    pool: adversarial
    query: "compare IF-0002 with all open RFQs"
    entry: { context: general, rfq_id: null }
    setup_assumption: "open RFQs slice resolves to ~30 items"
    expected:
      entry_path: "7"
      escalations:
        - trigger: ambiguous_target_count_exceeded  # cap N≤5
          to: "8.3_clarification"
      path: "8.3"
      finalizer_outcome: clarify
      clarification_template: "30 RFQs is too many to compare meaningfully — narrow by client, stage, or pick up to 5?"
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: clean
    tension: "Path 7 cap N≤5 enforced via existing trigger"

  - id: C10
    pool: adversarial
    query: "I asked yesterday about IF-0002, can you continue?"
    entry: { context: rfq_bound, rfq_id: "IF-0002" }
    setup_assumption: "last_activity on this thread > 7 days ago"
    expected:
      planner_behavior: "F7 — detect stale_conversation, spawn fresh thread for IF-0002, prepend system finalizer 'Starting a fresh conversation about IF-0002.', then classify the actual query"
      pre_classification_action: "fresh_thread_spawn"
      finalizer_prepend: "Starting a fresh conversation about IF-0002."
      then_classify_as: "4 or 5 depending on what 'continue' actually asks for"
      path: "8.3"  # if 'continue' is too vague → ambiguous → 8.3 clarification
    use_as_few_shot_for: [PathPlanner]
    result_phase_a: finding_F7
    tension: "F7 — stale handler now documented as Planner pre-classification behavior"
```

---

## Phase A summary

| Pool | Clean (post-correction) | Finding (pre-correction) |
|---|---|---|
| A — synthetic | 10 | 0 |
| B — realistic | 9 | 1 (B5 → F1) |
| C — adversarial | 4 | 6 (C1→F2, C3→F3, C5→F4, C7→F5, C8→F6, C10→F7) |
| **Total** | **23 / 30** | **7 / 30** |

After v1.1 corrections in `9-Path_Config_Table_v1.md`, all 30 queries trace to a defined behavior. Phase B (post-code execution) will validate that the implementation matches.

---

## Few-shot allocation

The following queries are flagged for inclusion as few-shot examples in production prompts:

**PathPlanner few-shots** (12): A2, A3, A4, A5, A6, A7, A8, A9, A10, B5, B10, C1, C2, C3, C5, C6, C7, C8, C9, C10
**Judge few-shots** (5): A7, A10, B3, C1, C4

Selection criteria: queries that exercise non-obvious classification (Pool A boundary cases, Pool C adversarial), or verify forbidden inference detection (B3, C4).

---

## Phase B — Post-code stress test (pending)

Once `PathPlanner`, `EscalationGate`, `EvidenceCheck`, and `Judge` are coded:

1. Load this YAML.
2. For each query, instantiate session state (`entry.context`, `entry.rfq_id`, `setup_assumption`).
3. Run the query through the full pipeline.
4. Compare actual outcomes (`actual.path`, `actual.escalations`, `actual.tools_called`, `actual.finalizer`) to `expected.*`.
5. Any mismatch is either a code bug OR a spec gap — diagnose case by case.
6. Apply findings to `9-Path_Config_Table_v1.md` (becomes v1.2) and re-run.

When phase B passes 30/30, `9-Path_Config_Table_v1.md` may be promoted to **frozen v1.0**.

---

*End of Stress Test Set v1.*
