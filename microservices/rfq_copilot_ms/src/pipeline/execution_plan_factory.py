"""ExecutionPlanFactory — Stage 2.5 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §2.7 and §3.2.

**The single chokepoint for ``TurnExecutionPlan`` construction.** No code
anywhere else in the repository may instantiate ``TurnExecutionPlan(...)``.
This invariant is mechanically enforced by CI guard §11.5.1 (AST grep).

The factory accepts three input shapes and produces one output:

* ``build_from_intake(decision, ...)``   -> ``TurnExecutionPlan``
* ``build_from_planner(validated, ...)`` -> ``TurnExecutionPlan | FactoryRejection``
* ``build_from_escalation(request, ...)`` -> ``TurnExecutionPlan``

Source-aware policy enforcement (§2.7):

============= =========================================================== ==========
Rule          Check                                                       On failure
============= =========================================================== ==========
F1            (path, intent_topic) exists in registry                     8.1
F2            IntakeSource in IntentConfig.allowed_intake_sources         8.1
F3            Field-alias normalization -> canonical_requested_fields     8.1
F4            canonical_requested_fields ⊆ allowed_fields ∪ forbidden     8.1
F5            canonical_requested_fields ∩ forbidden_fields == ∅          8.1
F6            confidence ≥ IntentConfig.confidence_threshold              8.3
F7            Path 7 only — ∩ comparable_field_groups.C == ∅              8.1
F8            Path 3 only — required_query_slots present in proposal      8.3
============= =========================================================== ==========

F6 applies to ``build_from_planner`` only (FastIntake is deterministic
regex; Escalation has no confidence).

Path 8.x handling (special-cased before F1):

* Direct planner emissions (8.1 / 8.2 / 8.3+multi_intent_detected) bypass
  F1 because Path 8.x configs declare empty ``intent_topics`` per Batch 2.
  Reason codes are mapped via ``_PLANNER_DIRECT_PATH_8_REASON_CODES``.
  PATH_8_4 / PATH_8_5 from a planner source are rejected by the
  PlannerValidator (rule 2d). If they slip through (e.g. tests), they
  fall to F1 and get rejected as ``unsupported_intent_topic``.

* FastIntake direct emissions (8.2 ``out_of_scope_nonsense`` and
  8.3 ``empty_message``) bypass F1 the same way; reason codes are
  mapped via ``_FAST_INTAKE_DIRECT_PATH_8_REASON_CODES``.

* Escalation Gate re-entries always target a Path 8.x sub-case via
  ``EscalationRequest.target_path`` + ``reason_code``. Looked up against
  ``PathConfig.finalizer_template_keys[reason_code]``. If the
  reason_code has no template, ``ValueError`` is raised loudly — the
  factory never invents a fallback template.

Plan ``intent_topic`` for Path 8.x: per Batch 2 spec, set to the
``reason_code`` string. Path 8.x configs declare no ``intent_topics`` in
the registry; the plan's ``intent_topic`` field still needs a value, and
``reason_code`` is the most informative one for forensics.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Registry CONFIG import is restricted to this module + escalation_gate.py
# by CI guard §11.5.2.
from src.config.path_registry import PATH_CONFIGS, REGISTRY_VERSION
from src.models.actor import Actor
from src.models.execution_plan import (
    EscalationRequest,
    FactoryRejection,
    TurnExecutionPlan,
)
from src.models.intake_decision import IntakeDecision
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    IntentConfig,
    PathConfig,
    PathId,
    PathRegistry,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
)
from src.models.planner_proposal import (
    PlannerProposal,
    ValidatedPlannerProposal,
)


# ── Path 8.x direct-emission mapping tables ───────────────────────────────


_PLANNER_DIRECT_PATH_8_REASON_CODES: dict[PathId, str] = {
    PathId.PATH_8_1: "unsupported_intent",
    PathId.PATH_8_2: "out_of_scope",
    # PATH_8_3 is conditional on multi_intent_detected — handled inline.
}

_FAST_INTAKE_DIRECT_PATH_8_REASON_CODES: dict[tuple[PathId, str], str] = {
    (PathId.PATH_8_2, "out_of_scope_nonsense"): "out_of_scope_nonsense",
    (PathId.PATH_8_3, "empty_message"): "empty_message",
}

_PATH_8_FAMILY = {
    PathId.PATH_8_1,
    PathId.PATH_8_2,
    PathId.PATH_8_3,
    PathId.PATH_8_4,
    PathId.PATH_8_5,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── ExecutionPlanFactory ──────────────────────────────────────────────────


class ExecutionPlanFactory:
    """The single ``TurnExecutionPlan`` constructor.

    CI guard §11.5.1 verifies that ``TurnExecutionPlan(...)`` is
    instantiated **only** in this module. CI guard §11.5.2 verifies
    that ``src.config.path_registry`` is imported **only** here and in
    ``escalation_gate.py``.

    Constructor takes the registry as a parameter so tests can inject
    synthetic registries (e.g. with a Path 7 entry to exercise rule
    F7, or a Path 3 entry to exercise rule F8) without mutating the
    production ``PATH_CONFIGS`` constant.
    """

    def __init__(
        self,
        registry: PathRegistry = PATH_CONFIGS,
        registry_version: str = REGISTRY_VERSION,
    ):
        self._registry: PathRegistry = registry
        self._registry_version: str = registry_version

    # ── Public build_from_* entry points ──────────────────────────────────

    def build_from_intake(
        self,
        decision: IntakeDecision,
        actor: Actor | None = None,  # noqa: ARG002 — wired for Resolver/Access
        session: object | None = None,  # noqa: ARG002 — SessionState lands later
    ) -> TurnExecutionPlan | FactoryRejection:
        """FastIntake source.

        FastIntake hits one of three paths in Slice 1:
        * Path 1 (greeting / thanks / farewell) — normal F1+F2 lookup.
        * Path 8.2 (out_of_scope_nonsense)      — direct emission.
        * Path 8.3 (empty_message)              — direct emission.
        """
        path = decision.path

        # Path 8.x direct emission shortcut (bypasses F1 — Path 8.x
        # configs declare empty intent_topics).
        if path in _PATH_8_FAMILY:
            reason_code = _FAST_INTAKE_DIRECT_PATH_8_REASON_CODES.get(
                (path, decision.intent_topic)
            )
            if reason_code is None:
                # FastIntake tried to emit a Path 8.x case it isn't
                # registered for. Treat as F1 failure — the (path,
                # intent_topic) pair has no entry.
                return self._reject(
                    trigger="unsupported_intent_topic",
                    reason_code="unsupported_intent",
                    factory_rule="F1",
                    rejected_input=None,
                )
            return self._build_path_8_plan(
                path=path,
                reason_code=ReasonCode(reason_code),
                source=IntakeSource.FAST_INTAKE,
            )

        # Normal path lookup (Path 1 only in Slice 1 for FastIntake).
        rejection = self._enforce_f1_f2_normal(
            path=path,
            intent_topic=decision.intent_topic,
            source=IntakeSource.FAST_INTAKE,
            rejected_input=None,
        )
        if rejection is not None:
            return rejection

        path_config = self._registry[path]
        intent_config = path_config.intent_topics[decision.intent_topic]

        # FastIntake has no requested_fields — trivial messages have no
        # field whitelist semantics. canonical_requested_fields = [].
        canonical_requested_fields: list[str] = []

        return self._build_normal_plan(
            path=path,
            intent_topic=decision.intent_topic,
            source=IntakeSource.FAST_INTAKE,
            path_config=path_config,
            intent_config=intent_config,
            target_candidates=[],
            canonical_requested_fields=canonical_requested_fields,
        )

    def build_from_planner(
        self,
        proposal: ValidatedPlannerProposal,
        actor: Actor | None = None,  # noqa: ARG002
        session: object | None = None,  # noqa: ARG002
    ) -> TurnExecutionPlan | FactoryRejection:
        """Planner+Validator source. May reject via F1..F7 (F6 specifically
        applies here only — FastIntake/Escalation have no confidence)."""
        inner: PlannerProposal = proposal.proposal
        path = inner.path

        # Path 8.x direct emission from the Planner. Validator rule 2
        # accepts 8.1 / 8.2 / 8.3+multi_intent. Validator rule 2c rejects
        # 8.3 without the flag, and rule 2d rejects 8.4 / 8.5 — so we
        # should only see {8_1, 8_2, 8_3+multi_intent} here. Defense in
        # depth: if 8.4 / 8.5 slip through, fall to F1 and reject as
        # unsupported_intent_topic.
        if path in _PATH_8_FAMILY:
            reason_code: str | None = None
            if path is PathId.PATH_8_3 and inner.multi_intent_detected:
                reason_code = "multi_intent_detected"
            else:
                reason_code = _PLANNER_DIRECT_PATH_8_REASON_CODES.get(path)
            if reason_code is None:
                # PATH_8_4 / PATH_8_5 (validator should have caught) OR
                # PATH_8_3 without multi_intent (validator should have caught).
                return self._reject(
                    trigger="unsupported_intent_topic",
                    reason_code="unsupported_intent",
                    factory_rule="F1",
                    rejected_input=proposal,
                )
            return self._build_path_8_plan(
                path=path,
                reason_code=ReasonCode(reason_code),
                source=IntakeSource.PLANNER,
            )

        # Normal path: F1 + F2 first.
        rejection = self._enforce_f1_f2_normal(
            path=path,
            intent_topic=inner.intent_topic,
            source=IntakeSource.PLANNER,
            rejected_input=proposal,
        )
        if rejection is not None:
            return rejection

        path_config = self._registry[path]
        intent_config = path_config.intent_topics[inner.intent_topic]

        # F3 — alias normalization (with empty-requested-fields default).
        canonical_or_rejection = self._normalize_fields(
            requested_fields=inner.requested_fields,
            intent_config=intent_config,
            path_config=path_config,
            rejected_input=proposal,
        )
        if isinstance(canonical_or_rejection, FactoryRejection):
            return canonical_or_rejection
        canonical_requested_fields: list[str] = canonical_or_rejection

        # F4 — canonical_requested_fields ⊆ allowed_fields ∪ forbidden_fields.
        # Defensive: F3 should have already rejected anything outside this
        # union, but a future config bug (e.g. an alias keying a canonical
        # that isn't in either list) could leak through. Catch it here.
        known_fields = set(intent_config.allowed_fields) | set(
            path_config.forbidden_fields
        )
        unknown = [f for f in canonical_requested_fields if f not in known_fields]
        if unknown:
            return self._reject(
                trigger="unsupported_field_requested",
                reason_code="unsupported_field_requested",
                factory_rule="F4",
                rejected_input=proposal,
            )

        # F5 — no forbidden fields requested.
        forbidden_hits = [
            f for f in canonical_requested_fields
            if f in path_config.forbidden_fields
        ]
        if forbidden_hits:
            return self._reject(
                trigger="forbidden_field_requested",
                reason_code="forbidden_field_requested",
                factory_rule="F5",
                rejected_input=proposal,
            )

        # F6 — confidence threshold (Planner-source only).
        if inner.confidence < intent_config.confidence_threshold:
            return self._reject(
                trigger="confidence_below_threshold",
                reason_code="confidence_below_threshold",
                factory_rule="F6",
                rejected_input=proposal,
            )

        # F7 — Path 7 Group C check (only fires if a Path 7 IntentConfig
        # is present in the registry with comparable_field_groups. Slice 1
        # PATH_CONFIGS doesn't include Path 7; tests inject a synthetic
        # registry to exercise this).
        if (
            path is PathId.PATH_7
            and intent_config.comparable_field_groups is not None
        ):
            group_c_hits = [
                f for f in canonical_requested_fields
                if f in intent_config.comparable_field_groups.C
            ]
            if group_c_hits:
                return self._reject(
                    trigger="group_C_field_requested",
                    reason_code="group_C_field_requested",
                    factory_rule="F7",
                    rejected_input=proposal,
                )

        # F8 — Path 3 required query slots (only fires if a Path 3
        # IntentConfig is present with required_query_slots. Same registry
        # injection pattern as F7).
        if path is PathId.PATH_3 and intent_config.required_query_slots:
            slot_present = {
                "filters": inner.filters is not None,
                "output_shape": inner.output_shape is not None,
                "sort": inner.sort is not None,
                "limit": inner.limit is not None,
            }
            missing = [
                s for s in intent_config.required_query_slots
                if not slot_present.get(s, False)
            ]
            if missing:
                return self._reject(
                    trigger="pre_search_query_underspecified",
                    reason_code="pre_search_query_underspecified",
                    factory_rule="F8",
                    rejected_input=proposal,
                )

        # All rules passed — build the trusted plan.
        return self._build_normal_plan(
            path=path,
            intent_topic=inner.intent_topic,
            source=IntakeSource.PLANNER,
            path_config=path_config,
            intent_config=intent_config,
            target_candidates=list(inner.target_candidates),
            canonical_requested_fields=canonical_requested_fields,
        )

    def build_from_escalation(
        self,
        request: EscalationRequest,
        actor: Actor | None = None,  # noqa: ARG002
        session: object | None = None,  # noqa: ARG002
    ) -> TurnExecutionPlan:
        """Escalation Gate re-entry. Always produces a Path 8.x plan.

        Looks up ``PATH_CONFIGS[request.target_path].finalizer_template_keys[request.reason_code]``.
        Raises ``ValueError`` loudly if the reason_code has no template
        — the factory never invents a fallback.
        """
        target_path = request.target_path
        reason_code = request.reason_code

        if target_path not in self._registry:
            raise ValueError(
                f"EscalationRequest target_path {target_path!r} is not in "
                f"the registry. The Escalation Gate must only target Path "
                f"8.x sub-cases declared in PATH_CONFIGS."
            )

        path_config = self._registry[target_path]
        if reason_code not in path_config.finalizer_template_keys:
            raise ValueError(
                f"EscalationRequest reason_code {reason_code!r} has no "
                f"finalizer template under {target_path!r}. Available "
                f"reason_codes: {sorted(path_config.finalizer_template_keys)}. "
                f"Add the template to src/config/path_registry.py "
                f"PATH_CONFIGS[{target_path!r}].finalizer_template_keys."
            )

        return self._build_path_8_plan(
            path=target_path,
            reason_code=reason_code,
            source=IntakeSource.ESCALATION,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _enforce_f1_f2_normal(
        self,
        *,
        path: PathId,
        intent_topic: str,
        source: IntakeSource,
        rejected_input: ValidatedPlannerProposal | None,
    ) -> FactoryRejection | None:
        """F1 + F2 for normal (non-Path-8) paths. Returns None on pass."""
        # F1 — (path, intent_topic) exists in registry.
        path_config = self._registry.get(path)
        if path_config is None or intent_topic not in path_config.intent_topics:
            return self._reject(
                trigger="unsupported_intent_topic",
                reason_code="unsupported_intent",
                factory_rule="F1",
                rejected_input=rejected_input,
            )

        # F2 — IntakeSource in IntentConfig.allowed_intake_sources.
        intent_config = path_config.intent_topics[intent_topic]
        if source not in intent_config.allowed_intake_sources:
            return self._reject(
                trigger="intake_source_not_allowed",
                reason_code="intake_source_not_allowed",
                factory_rule="F2",
                rejected_input=rejected_input,
            )

        return None

    def _normalize_fields(
        self,
        *,
        requested_fields: list[str],
        intent_config: IntentConfig,
        path_config: PathConfig,
        rejected_input: ValidatedPlannerProposal,
    ) -> list[str] | FactoryRejection:
        """F3 — alias normalization with empty-default behavior.

        * If ``requested_fields`` is empty, default to
          ``intent_config.allowed_fields`` (the safe assumption — if the
          planner emits intent_topic="deadline" without listing fields,
          we fetch the deadline).
        * Exact canonical names pass through.
        * Known aliases map to their canonical name.
        * Unknown entries reject as F3 ``unsupported_field_requested``.
        """
        if not requested_fields:
            return list(intent_config.allowed_fields)

        # Build the inverse alias map: alias_text -> canonical_name.
        inverse_aliases: dict[str, str] = {}
        for canonical, aliases in intent_config.field_aliases.items():
            for alias in aliases:
                inverse_aliases[alias] = canonical

        known_canonicals = set(intent_config.allowed_fields) | set(
            path_config.forbidden_fields
        )

        canonical_out: list[str] = []
        for requested in requested_fields:
            if requested in known_canonicals:
                canonical_out.append(requested)
                continue
            if requested in inverse_aliases:
                canonical_out.append(inverse_aliases[requested])
                continue
            # Unknown — never guess.
            return self._reject(
                trigger="unsupported_field_requested",
                reason_code="unsupported_field_requested",
                factory_rule="F3",
                rejected_input=rejected_input,
            )

        return canonical_out

    def _select_finalizer_template_key(
        self,
        *,
        path_config: PathConfig,
        intent_topic: str,
    ) -> str:
        """Normal-path template selection per Batch 2 keying convention:

        * If ``finalizer_template_keys[intent_topic]`` exists, use it.
          (Path 1 keys per intent_topic.)
        * Else use ``finalizer_template_key_default``. (Path 4 single
          template for the path.)
        * Else the PathConfig validator would have rejected at registry
          load time — but defensively raise ValueError here too.
        """
        if intent_topic in path_config.finalizer_template_keys:
            return path_config.finalizer_template_keys[intent_topic]
        if path_config.finalizer_template_key_default is not None:
            return path_config.finalizer_template_key_default
        raise ValueError(
            f"PathConfig has neither finalizer_template_keys[{intent_topic!r}] "
            f"nor finalizer_template_key_default. The PathConfig validator "
            f"should have caught this at registry load time."
        )

    def _build_normal_plan(
        self,
        *,
        path: PathId,
        intent_topic: str,
        source: IntakeSource,
        path_config: PathConfig,
        intent_config: IntentConfig,
        target_candidates: list,
        canonical_requested_fields: list[str],
    ) -> TurnExecutionPlan:
        """Construct a normal-answer-path TurnExecutionPlan from the
        registry. The ONLY place ``TurnExecutionPlan(...)`` is called
        for non-Path-8 cases. CI guard §11.5.1 enforces uniqueness.
        """
        template_key = self._select_finalizer_template_key(
            path_config=path_config,
            intent_topic=intent_topic,
        )

        return TurnExecutionPlan(
            path=path,
            intent_topic=intent_topic,
            source=source,
            target_candidates=target_candidates,
            resolver_strategy=path_config.resolver_strategy,
            required_target_policy=(
                path_config.required_target_policy
                if path_config.required_target_policy is not None
                else TargetPolicy.none()
            ),
            allowed_evidence_tools=list(intent_config.evidence_tools),
            allowed_resolver_tools=list(path_config.allowed_resolver_tools),
            access_policy=path_config.access_policy,
            allowed_fields=list(intent_config.allowed_fields),
            forbidden_fields=list(path_config.forbidden_fields),
            canonical_requested_fields=canonical_requested_fields,
            active_guardrails=list(path_config.active_guardrails),
            judge_policy=path_config.judge_policy,
            memory_policy=path_config.memory_policy,
            persistence_policy=path_config.persistence_policy,
            finalizer_template_key=template_key,
            finalizer_reason_code=None,
            model_profile=path_config.model_profile,
            min_accessible_targets_for_comparison=(
                intent_config.min_accessible_targets_for_comparison
            ),
            comparable_field_groups=intent_config.comparable_field_groups,
        )

    def _build_path_8_plan(
        self,
        *,
        path: PathId,
        reason_code: ReasonCode,
        source: IntakeSource,
    ) -> TurnExecutionPlan:
        """Construct a minimal Path 8.x TurnExecutionPlan. Template key
        comes from ``PATH_CONFIGS[path].finalizer_template_keys[reason_code]``.
        Plan ``intent_topic`` is set to the reason_code string per Batch 2
        spec (Path 8.x configs declare no intent_topics).
        """
        if path not in self._registry:
            raise ValueError(
                f"Path 8.x path {path!r} is not in the registry."
            )
        path_config = self._registry[path]
        if reason_code not in path_config.finalizer_template_keys:
            raise ValueError(
                f"Reason code {reason_code!r} has no finalizer template "
                f"under {path!r}. Available: "
                f"{sorted(path_config.finalizer_template_keys)}."
            )

        template_key = path_config.finalizer_template_keys[reason_code]

        return TurnExecutionPlan(
            path=path,
            intent_topic=str(reason_code),  # Path 8 plans use reason_code as intent_topic
            source=source,
            target_candidates=[],
            resolver_strategy=ResolverStrategy.NONE,
            required_target_policy=TargetPolicy.none(),
            allowed_evidence_tools=[],
            allowed_resolver_tools=[],
            access_policy=AccessPolicyName.NONE,
            allowed_fields=[],
            forbidden_fields=[],
            canonical_requested_fields=[],
            active_guardrails=[],
            judge_policy=None,
            memory_policy=path_config.memory_policy,
            persistence_policy=path_config.persistence_policy,
            finalizer_template_key=template_key,
            finalizer_reason_code=reason_code,
            model_profile=None,
            min_accessible_targets_for_comparison=None,
            comparable_field_groups=None,
        )

    @staticmethod
    def _reject(
        *,
        trigger: str,
        reason_code: str,
        factory_rule: str,
        rejected_input: ValidatedPlannerProposal | None,
    ) -> FactoryRejection:
        """Construct a FactoryRejection.

        ``rejected_input`` may be None for FastIntake-source rejections
        (no ValidatedPlannerProposal exists in that flow). The
        FactoryRejection model requires a non-None
        ``rejected_input``; for FastIntake, callers must handle this
        differently — see _reject_intake() if needed.
        """
        if rejected_input is None:
            # FastIntake-source rejection. The FactoryRejection model
            # requires a ValidatedPlannerProposal; we don't have one.
            # Construct a placeholder to keep the type contract intact —
            # forensics will show the FastIntake source via factory_rule
            # context.
            #
            # Long-term: FactoryRejection.rejected_input could be widened
            # to Union[ValidatedPlannerProposal, IntakeDecision]. For
            # Slice 1 we keep the current type and document this via the
            # factory_rule field.
            from src.models.planner_proposal import PlannerProposal as _PP
            placeholder_proposal = _PP(
                path=PathId.PATH_8_1,
                intent_topic="__fast_intake_factory_rejection__",
                confidence=0.0,
                classification_rationale="FastIntake-source factory rejection placeholder.",
            )
            from datetime import datetime as _dt, timezone as _tz
            placeholder = ValidatedPlannerProposal(
                proposal=placeholder_proposal,
                validated_at=_dt.now(_tz.utc),
            )
            rejected_input = placeholder

        return FactoryRejection(
            trigger=trigger,
            reason_code=ReasonCode(reason_code),
            rejected_input=rejected_input,
            factory_rule=factory_rule,  # type: ignore[arg-type]
            rejected_at=_utc_now(),
        )
