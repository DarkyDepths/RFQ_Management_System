"""Path Registry — runtime CONFIG (§3.1, §14.2 + Slice 1 scope).

================================================================
"Path Registry" = two complementary modules. This is the CONFIG half.
================================================================

* **Sibling — ``src/models/path_registry.py``** (TYPES)
  Pure declarations: ``PathId``, ``IntakeSource``, ``IntentConfig``,
  ``PathConfig``, etc. Importable from anywhere.

* **This module — ``src/config/path_registry.py``** (CONFIG)
  The runtime ``PATH_CONFIGS: PathRegistry`` data table — the actual
  policy table read at plan-build time. **Restricted to
  ``ExecutionPlanFactory`` and ``EscalationGate`` only**, CI-enforced
  by ``tests/anti_drift/test_path_registry_reader_allowlist.py``
  (§11.5.2). Importing this module gives the importer the ability to
  enforce or bypass policy — that's the chokepoint the architecture
  protects.

The split is the architectural commitment: types travel freely, policy
data does not.

================================================================
Slice 1 scope (this batch)
================================================================

Active paths in Slice 1:

* **Path 1** — conversational trivial messages (greeting, thanks,
  farewell). Both FastIntake and Planner may emit. Template-only.
* **Path 4** — RFQ-specific operational retrieval. Planner-only intake.
  Manager-mediated access. Eight intent topics covering the canonical
  manager DTO fields (deadline, owner, status, current_stage,
  priority, blockers, stages, summary).
* **Path 8.1 / 8.2 / 8.3 / 8.4 / 8.5** — safety / escalation paths.
  Template-only. ``finalizer_template_keys`` keyed by ``reason_code``
  per the §6 escalation matrix.

**Absent paths (2, 3, 5, 6, 7).** Not configured here. The Batch 3
``ExecutionPlanFactory`` rule F1 will see the missing key and emit
``unsupported_intent_topic`` -> 8.1 for any planner proposal targeting
these paths. This is per spec — "do not invent placeholder model
fields"; absence + factory routing is the agreed mechanism.

================================================================
finalizer_template_keys keying convention
================================================================

The ``PathConfig.finalizer_template_keys`` dict is keyed differently
depending on the path family:

* **Normal answer paths (Path 1 in Slice 1)** — keyed by
  ``intent_topic`` (e.g. ``"greeting"`` -> ``"path_1.greeting"``). The
  factory copies ``intent_topic`` into the plan and the Finalizer
  picks the template by intent.
* **Path 8.x safety paths** — keyed by ``reason_code`` (e.g.
  ``"no_evidence"`` -> ``"path_8_5.no_evidence"``). The Escalation
  Gate sets ``finalizer_reason_code`` on the Path 8.x plan; the
  Finalizer picks by reason_code.
* **Path 4** — uses ``finalizer_template_key_default`` (one template
  for the whole path, intent-aware rendering happens inside the
  Finalizer). Per-intent template-first §12.6 is deferred to a later
  batch (would require extending ``IntentConfig`` with a per-intent
  ``model_profile`` / ``template_key`` override).

The Batch 3 factory will encode the dual semantics: normal paths key
on ``intent_topic``, Path 8.x key on ``reason_code``. No type changes
needed — both are strings on the same ``finalizer_template_keys`` dict.

================================================================
Discipline rules for this module
================================================================

* No functions with behavior. Pure constants only.
* No wrapper class. ``PATH_CONFIGS`` is a plain ``dict``.
* No dynamic loading. No env reads. No I/O.
* No imports from ``src/pipeline/`` (would be a circular dependency
  and would also defeat the chokepoint).
* No manager / LLM / network calls.
* Type imports from ``src.models.path_registry`` only.
"""

from __future__ import annotations

from src.models.path_registry import (
    AccessPolicyName,
    GuardrailId,
    IntakeSource,
    IntentConfig,
    JudgePolicy,
    JudgeTriggerName,
    MemoryPolicy,
    ModelProfile,
    PathConfig,
    PathId,
    PathRegistry,
    PersistencePolicy,
    PlannerModelConfig,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)


REGISTRY_VERSION: str = "0.1.0-slice1"
"""Semver of the registry config table at build time. Changes whenever
``PATH_CONFIGS`` shape changes (new path, new intent, new field, new
reason_code). Slice 2 may bump to a higher minor when adding paths or
intents; major bumps for incompatible reshapes."""


# ── Top-level Planner config (§3.5) ───────────────────────────────────────


PLANNER_MODEL_CONFIG: PlannerModelConfig = PlannerModelConfig(
    model="gpt-4o",
    temperature=0.0,
    max_tokens=800,
    timeout_seconds=15.0,
    json_schema_enforced=True,
    retry_attempts=1,
)
"""Used BEFORE the path is known (§3.5). Cannot be derived from any
per-path ``PathConfig.model_profile`` — the Planner classifies the turn
into a path, so by definition no path has been chosen yet."""


# ── Internal reusable policy fragments (private — leading underscore) ─────


_PERSISTENCE_TEMPLATE_ONLY: PersistencePolicy = PersistencePolicy(
    store_user_msg=True,
    store_assistant_msg=True,
    store_tool_calls=False,        # template-only paths run no tools
    store_source_refs=False,
    store_judge_verdict=False,     # judge skipped on template-only paths
    episodic_contribution=False,   # trivial messages don't enrich episodic memory
    update_last_activity=True,
    session_state_writes=[],
)
"""Persistence policy for template-only paths (Path 1 conversational +
all Path 8.x except 8.3). Records the turn for forensics; contributes
nothing to long-term memory."""


_PERSISTENCE_CLARIFICATION: PersistencePolicy = PersistencePolicy(
    store_user_msg=True,
    store_assistant_msg=True,
    store_tool_calls=False,
    store_source_refs=False,
    store_judge_verdict=False,
    episodic_contribution=False,
    update_last_activity=True,
    session_state_writes=["pending_clarification"],
)
"""Path 8.3 specifically — writes ``pending_clarification`` to
session_state per freeze §3.1 example, so the next turn can re-classify
in the context of the clarification request."""


_PERSISTENCE_PATH_4: PersistencePolicy = PersistencePolicy(
    store_user_msg=True,
    store_assistant_msg=True,
    store_tool_calls=True,         # Path 4 calls manager tools
    store_source_refs=True,
    store_judge_verdict=True,
    episodic_contribution=True,
    update_last_activity=True,
    session_state_writes=[],
)
"""Path 4 full operational persistence — tool calls + source refs +
judge verdict + episodic contribution. Forensics for "why did the
copilot say what it said about IF-0001"."""


_MEMORY_PATH_1: MemoryPolicy = MemoryPolicy(
    working_pairs=2,
    episodic_scope="none",
)
"""Path 1 conversational memory — minimal recent context, no episodic
contribution. A greeting is not worth carrying forward."""


_MEMORY_PATH_4: MemoryPolicy = MemoryPolicy(
    working_pairs=5,
    episodic_scope="per_target",
)
"""Path 4 working memory + per-target episodic scope per freeze §3.1
example. "What about its priority?" after "When is IF-0001 due?" must
remember the target."""


_PATH_4_FORBIDDEN_FIELDS: list[str] = [
    "margin",
    "bid_amount",
    "internal_cost",
    "win_probability",
    "ranking",
    "winner",
    "estimation_quality",
]
"""Union of freeze §3.1 Path 4 example forbidden_fields and §14.2
Group C judgment fields. The factory rule F5 rejects any
``canonical_requested_fields`` ∩ this list -> 8.1
``forbidden_field_requested``."""


_PATH_4_MODEL_PROFILE: ModelProfile = ModelProfile(
    model="gpt-4o",
    temperature=0.3,
    max_tokens=500,
    timeout_seconds=30.0,
)
"""Path-level Compose profile for Path 4 (§3.1 example). Per-intent
template-first §12.6 (e.g. ``deadline`` should skip Compose) is DEFERRED
to a later batch — it would require extending ``IntentConfig`` with a
per-intent ``model_profile`` override. For Slice 1 / Batch 2 every Path
4 intent goes through Compose."""


_PATH_4_JUDGE_POLICY: JudgePolicy = JudgePolicy(
    triggers=[
        JudgeTriggerName("answer_makes_factual_claim"),
        JudgeTriggerName("answer_volunteers_unrelated_facts"),
    ],
    model_profile="gpt-4o",
    timeout_seconds=10.0,
)
"""Path 4 judge — catches factual claims that aren't grounded in
``evidence_packets`` and answers that volunteer fields the user didn't
ask for (a "agreeable LLM" mitigation per Risk 4 §7)."""


# ── Path 1 — Conversational ───────────────────────────────────────────────

# Both FastIntake (anchored regex) and Planner (more elaborate phrasings
# like "good morning" or "thanks for the help") may emit Path 1 intents.

_INTENT_GREETING: IntentConfig = IntentConfig(
    allowed_intake_sources=[IntakeSource.FAST_INTAKE, IntakeSource.PLANNER],
    evidence_tools=[],
    rag_required=False,
    allowed_fields=[],
    confidence_threshold=0.5,
    judge_triggers=[],
)

_INTENT_THANKS: IntentConfig = IntentConfig(
    allowed_intake_sources=[IntakeSource.FAST_INTAKE, IntakeSource.PLANNER],
    evidence_tools=[],
    rag_required=False,
    allowed_fields=[],
    confidence_threshold=0.5,
    judge_triggers=[],
)

_INTENT_FAREWELL: IntentConfig = IntentConfig(
    allowed_intake_sources=[IntakeSource.FAST_INTAKE, IntakeSource.PLANNER],
    evidence_tools=[],
    rag_required=False,
    allowed_fields=[],
    confidence_threshold=0.5,
    judge_triggers=[],
)


# ── Path 4 — RFQ-specific operational retrieval ───────────────────────────

# Tool-id convention: ``get_rfq_profile`` and ``get_rfq_stages`` match the
# freeze §3.1 examples. Slice 5 Tool Executor will map these to the
# manager connector's ``get_rfq_detail`` and ``get_rfq_stages`` methods.
# Tool ids are CONFIG-level aliases, not Python method names.

_TOOL_GET_RFQ_PROFILE: ToolId = ToolId("get_rfq_profile")
_TOOL_GET_RFQ_STAGES: ToolId = ToolId("get_rfq_stages")


def _planner_only_intent(
    *,
    evidence_tools: list[ToolId],
    allowed_fields: list[str],
    field_aliases: dict[str, list[str]],
) -> IntentConfig:
    """Path 4 IntentConfig builder — Planner-only intake, manager fields.

    Local helper used to keep the registry literal compact and consistent.
    Not exported. No behavior beyond IntentConfig construction.
    """
    return IntentConfig(
        allowed_intake_sources=[IntakeSource.PLANNER],
        evidence_tools=evidence_tools,
        rag_required=False,
        allowed_fields=allowed_fields,
        field_aliases=field_aliases,
        confidence_threshold=0.75,
        judge_triggers=[
            JudgeTriggerName("answer_makes_factual_claim"),
            JudgeTriggerName("answer_volunteers_unrelated_facts"),
        ],
    )


_INTENT_DEADLINE: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=["deadline"],
    field_aliases={
        "deadline": ["due date", "submission deadline", "submission date", "due"],
    },
)

_INTENT_OWNER: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=["owner"],
    field_aliases={
        "owner": ["who owns it", "owner name", "owned by"],
    },
)

_INTENT_STATUS: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=["status"],
    field_aliases={
        "status": ["state", "where it stands"],
    },
)

_INTENT_CURRENT_STAGE: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=["current_stage_name"],
    field_aliases={
        "current_stage_name": ["current stage", "where is it", "stage name"],
    },
)

_INTENT_PRIORITY: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=["priority"],
    field_aliases={
        "priority": ["how urgent", "priority level", "urgency"],
    },
)

_INTENT_BLOCKERS: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_STAGES],
    allowed_fields=["blocker_status", "blocker_reason_code"],
    field_aliases={
        "blocker_status": ["blockers", "is it blocked", "any blocker"],
    },
)

_INTENT_STAGES: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_STAGES],
    allowed_fields=["name", "order", "status"],
    field_aliases={
        "name": ["stage list", "all stages", "workflow stages"],
    },
)

_INTENT_SUMMARY: IntentConfig = _planner_only_intent(
    evidence_tools=[_TOOL_GET_RFQ_PROFILE],
    allowed_fields=[
        "name",
        "client",
        "status",
        "priority",
        "deadline",
        "current_stage_name",
    ],
    field_aliases={
        "name": ["overview", "snapshot", "brief"],
    },
)


# ── PATH_CONFIGS ──────────────────────────────────────────────────────────


PATH_CONFIGS: PathRegistry = {
    PathId.PATH_1: PathConfig(
        intent_topics={
            "greeting": _INTENT_GREETING,
            "thanks": _INTENT_THANKS,
            "farewell": _INTENT_FAREWELL,
        },
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=_MEMORY_PATH_1,
        persistence_policy=_PERSISTENCE_TEMPLATE_ONLY,
        active_guardrails=[],
        judge_policy=None,
        # Per-intent template keys (Path 1 keying convention — see
        # module docstring). Factory copies plan.intent_topic; Finalizer
        # picks by intent.
        finalizer_template_keys={
            "greeting": "path_1.greeting",
            "thanks": "path_1.thanks",
            "farewell": "path_1.farewell",
        },
        finalizer_template_key_default=None,
        model_profile=None,  # template-only
    ),
    PathId.PATH_4: PathConfig(
        intent_topics={
            "deadline": _INTENT_DEADLINE,
            "owner": _INTENT_OWNER,
            "status": _INTENT_STATUS,
            "current_stage": _INTENT_CURRENT_STAGE,
            "priority": _INTENT_PRIORITY,
            "blockers": _INTENT_BLOCKERS,
            "stages": _INTENT_STAGES,
            "summary": _INTENT_SUMMARY,
        },
        resolver_strategy=ResolverStrategy.SEARCH_BY_CODE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy(
            min_targets=1,
            max_targets=1,
        ),
        access_policy=AccessPolicyName.MANAGER_MEDIATED,
        forbidden_fields=_PATH_4_FORBIDDEN_FIELDS,
        memory_policy=_MEMORY_PATH_4,
        persistence_policy=_PERSISTENCE_PATH_4,
        active_guardrails=[
            GuardrailId("evidence"),
            GuardrailId("forbidden_field"),
            GuardrailId("internal_label"),
            GuardrailId("scope"),
            GuardrailId("shape"),
        ],
        judge_policy=_PATH_4_JUDGE_POLICY,
        finalizer_template_keys={},
        finalizer_template_key_default="path_4.default",
        model_profile=_PATH_4_MODEL_PROFILE,
    ),
    PathId.PATH_8_1: PathConfig(
        # Unsupported / invalid — terminal template-only.
        intent_topics={},
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=None,
        persistence_policy=_PERSISTENCE_TEMPLATE_ONLY,
        active_guardrails=[],
        judge_policy=None,
        finalizer_template_keys={
            "unsupported_intent": "path_8_1.unsupported_intent",
            "unsupported_intent_topic": "path_8_1.unsupported_intent_topic",
            "unsupported_field_requested": "path_8_1.unsupported_field",
            "forbidden_field_requested": "path_8_1.forbidden_field",
            "intake_source_not_allowed": "path_8_1.intake_source_not_allowed",
            "invalid_planner_proposal": "path_8_1.invalid_proposal",
            "group_C_field_requested": "path_8_1.group_c_field",
        },
        finalizer_template_key_default=None,
        model_profile=None,
    ),
    PathId.PATH_8_2: PathConfig(
        # Out-of-scope — terminal template-only.
        intent_topics={},
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=None,
        persistence_policy=_PERSISTENCE_TEMPLATE_ONLY,
        active_guardrails=[],
        judge_policy=None,
        finalizer_template_keys={
            "out_of_scope": "path_8_2.out_of_scope",
            "out_of_scope_nonsense": "path_8_2.out_of_scope_nonsense",
            "judge_scope_drift": "path_8_2.scope_drift",
        },
        finalizer_template_key_default=None,
        model_profile=None,
    ),
    PathId.PATH_8_3: PathConfig(
        # Clarification — writes session_state.pending_clarification.
        intent_topics={},
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=None,
        persistence_policy=_PERSISTENCE_CLARIFICATION,
        active_guardrails=[],
        judge_policy=None,
        finalizer_template_keys={
            "unclear_intent_topic": "path_8_3.unclear_intent",
            "confidence_below_threshold": "path_8_3.low_confidence",
            "no_target_proposed": "path_8_3.no_target",
            "no_target": "path_8_3.no_target",
            "comparison_missing_target": "path_8_3.comparison_missing_target",
            "ambiguous_target_count_exceeded": "path_8_3.ambiguous",
            "ambiguous": "path_8_3.ambiguous",
            "multi_intent_detected": "path_8_3.multi_intent",
            "pre_search_query_underspecified": "path_8_3.pre_search_underspecified",
            "post_search_no_safe_presentation": "path_8_3.post_search_unrenderable",
            "empty_message": "path_8_3.empty_message",
        },
        finalizer_template_key_default=None,
        model_profile=None,
    ),
    PathId.PATH_8_4: PathConfig(
        # Inaccessible — terminal template-only.
        intent_topics={},
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=None,
        persistence_policy=_PERSISTENCE_TEMPLATE_ONLY,
        active_guardrails=[],
        judge_policy=None,
        finalizer_template_keys={
            "access_denied_explicit": "path_8_4.denied",
            "all_inaccessible": "path_8_4.all_inaccessible",
            "partial": "path_8_4.partial",
            "partial_inaccessibility_below_min": "path_8_4.partial_below_min",
        },
        finalizer_template_key_default=None,
        model_profile=None,
    ),
    PathId.PATH_8_5: PathConfig(
        # No-evidence / source-down / llm-down / judge-failed / budget-exceeded.
        intent_topics={},
        resolver_strategy=ResolverStrategy.NONE,
        allowed_resolver_tools=[],
        required_target_policy=TargetPolicy.none(),
        access_policy=AccessPolicyName.NONE,
        forbidden_fields=[],
        memory_policy=None,
        persistence_policy=_PERSISTENCE_TEMPLATE_ONLY,
        active_guardrails=[],
        judge_policy=None,
        finalizer_template_keys={
            "no_evidence": "path_8_5.no_evidence",
            "source_unavailable": "path_8_5.source_unavailable",
            # Manager 401 — distinct template so operators see a
            # deployment misconfig, not a generic "source is down"
            # (Batch 9.1).
            "manager_auth_failed": "path_8_5.manager_auth_failed",
            "llm_unavailable": "path_8_5.llm_unavailable",
            "judge_verdict_fabrication": "path_8_5.fabrication",
            "judge_verdict_forbidden_inference": "path_8_5.forbidden_inference",
            "judge_verdict_unsourced_citation": "path_8_5.unsourced_citation",
            "judge_verdict_comparison_violation": "path_8_5.comparison_violation",
            "target_isolation_violation": "path_8_5.target_isolation_violation",
            "forbidden_inference_detected_deterministic": "path_8_5.forbidden_inference_deterministic",
            "ambiguity_loop_max_reached": "path_8_5.ambiguity_loop",
            "turn_too_slow": "path_8_5.turn_too_slow",
        },
        finalizer_template_key_default=None,
        model_profile=None,
    ),
}
"""Slice 1 active registry. Paths 2, 3, 5, 6, 7 are intentionally
absent — Batch 3 ``ExecutionPlanFactory`` rule F1 (intent_topic exists
in registry) will reject any planner proposal targeting those paths
and the Escalation Gate routes to 8.1 ``unsupported_intent_topic``.

Bump ``REGISTRY_VERSION`` whenever this dict's shape changes."""
